# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickGear.
#
# SickGear is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickGear is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickGear.  If not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict

import datetime
import re
import threading
import time
import traceback

import sickbeard
from . import db, helpers, logger, name_cache
from .anime import create_anidb_obj
from .classes import OrderedDefaultdict
from .indexers.indexer_config import TVINFO_TVDB

from _23 import filter_iter, map_iter
from six import iteritems, PY2, text_type

# noinspection PyUnreachableCode
if False:
    # noinspection PyUnresolvedReferences
    from typing import AnyStr, List, Tuple

exception_dict = {}
anidb_exception_dict = {}
xem_exception_dict = {}
xem_ids_list = defaultdict(list)

exceptionsCache = {}
exceptionsSeasonCache = {}

exceptionLock = threading.Lock()


def should_refresh(name):
    """

    :param name: name
    :type name: AnyStr
    :return:
    :rtype: bool
    """
    max_refresh_age_secs = 86400  # 1 day

    my_db = db.DBConnection()
    rows = my_db.select('SELECT last_refreshed FROM scene_exceptions_refresh WHERE list = ?', [name])
    if rows:
        last_refresh = int(rows[0]['last_refreshed'])
        return int(time.mktime(datetime.datetime.today().timetuple())) > last_refresh + max_refresh_age_secs
    return True


def set_last_refresh(name):
    """

    :param name: name
    :type name: AnyStr
    """
    my_db = db.DBConnection()
    my_db.upsert('scene_exceptions_refresh',
                 {'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple()))},
                 {'list': name})


def get_scene_exceptions(tvid, prodid, season=-1):
    """
    Given a indexer_id, return a list of all the scene exceptions.
    :param tvid: tvid
    :type tvid: int
    :param prodid: prodid
    :type prodid: int or long
    :param season: season number
    :type season: int
    :return:
    :rtype: List
    """
    global exceptionsCache
    exceptions_list = []

    if (tvid, prodid) not in exceptionsCache or season not in exceptionsCache[(tvid, prodid)]:
        my_db = db.DBConnection()
        exceptions = my_db.select('SELECT show_name'
                                  ' FROM scene_exceptions'
                                  ' WHERE indexer = ? AND indexer_id = ?'
                                  ' AND season = ?',
                                  [tvid, prodid, season])
        if exceptions:
            exceptions_list = list(set([cur_exception['show_name'] for cur_exception in exceptions]))

            if (tvid, prodid) not in exceptionsCache:
                exceptionsCache[(tvid, prodid)] = {}
            exceptionsCache[(tvid, prodid)][season] = exceptions_list
    else:
        exceptions_list = exceptionsCache[(tvid, prodid)][season]

    if 1 == season:  # if we where looking for season 1 we can add generic names
        exceptions_list += get_scene_exceptions(tvid, prodid, season=-1)

    return exceptions_list


def get_all_scene_exceptions(tvid_prodid):
    """

    :param tvid_prodid:
    :type tvid_prodid: AnyStr
    :return:
    :rtype: OrderedDefaultdict
    """
    exceptions_dict = OrderedDefaultdict(list)

    from sickbeard.tv import TVidProdid

    my_db = db.DBConnection()
    exceptions = my_db.select('SELECT show_name,season'
                              ' FROM scene_exceptions'
                              ' WHERE indexer = ? AND indexer_id = ?'
                              ' ORDER BY season',
                              TVidProdid(tvid_prodid).list)

    if exceptions:
        for cur_exception in exceptions:
            exceptions_dict[cur_exception['season']].append(cur_exception['show_name'])

    return exceptions_dict


def get_scene_seasons(tvid, prodid):
    """
    return a list of season numbers that have scene exceptions
    :param tvid: tvid
    :type tvid: int
    :param prodid: prodid
    :type prodid: int or long
    :return:
    :rtype: List
    """
    global exceptionsSeasonCache
    exception_season_list = []

    if (tvid, prodid) not in exceptionsSeasonCache:
        my_db = db.DBConnection()
        sql_result = my_db.select('SELECT DISTINCT(season) AS season'
                                  ' FROM scene_exceptions'
                                  ' WHERE indexer = ? AND indexer_id = ?',
                                  [tvid, prodid])
        if sql_result:
            exception_season_list = list(set([int(x['season']) for x in sql_result]))

            if (tvid, prodid) not in exceptionsSeasonCache:
                exceptionsSeasonCache[(tvid, prodid)] = {}

            exceptionsSeasonCache[(tvid, prodid)] = exception_season_list
    else:
        exception_season_list = exceptionsSeasonCache[(tvid, prodid)]

    return exception_season_list


def get_scene_exception_by_name(show_name):
    """

    :param show_name: show name
    :type show_name: AnyStr
    :return:
    :rtype: Tuple[None, None, None] or Tuple[int, int or long, int]
    """
    return get_scene_exception_by_name_multiple(show_name)[0]


def get_scene_exception_by_name_multiple(show_name):
    """

    :param show_name: show name
    :type show_name: AnyStr
    :return:  (tvid, prodid, season) of the exception, None if no exception is present.
    :rtype: Tuple[None, None, None] or Tuple[int, int or long, int]
    """
    try:
        exception_result = name_cache.nameCache[helpers.full_sanitize_scene_name(show_name)]
        return [exception_result]
    except (BaseException, Exception):
        return [[None, None, None]]


def retrieve_exceptions():
    """
    Looks up the exceptions on github, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Also clears the scene name cache.
    """
    global exception_dict, anidb_exception_dict, xem_exception_dict

    # exceptions are stored on github pages
    for tvid in sickbeard.TVInfoAPI().sources:
        if should_refresh(sickbeard.TVInfoAPI(tvid).name):
            logger.log(u'Checking for scene exception updates for %s' % sickbeard.TVInfoAPI(tvid).name)

            url = sickbeard.TVInfoAPI(tvid).config['scene_url']

            url_data = helpers.get_url(url)
            if None is url_data:
                # When None is urlData, trouble connecting to github
                logger.log(u'Check scene exceptions update failed. Unable to get URL: %s' % url, logger.ERROR)
                continue

            else:
                set_last_refresh(sickbeard.TVInfoAPI(tvid).name)

                # each exception is on one line with the format indexer_id: 'show name 1', 'show name 2', etc
                for cur_line in url_data.splitlines():
                    cur_line = cur_line
                    prodid, sep, aliases = cur_line.partition(':')

                    if not aliases:
                        continue

                    prodid = int(prodid)

                    # regex out the list of shows, taking \' into account
                    # alias_list = [re.sub(r'\\(.)', r'\1', x) for x in re.findall(r"'(.*?)(?<!\\)',?", aliases)]
                    alias_list = [{re.sub(r'\\(.)', r'\1', x): -1} for x in re.findall(r"'(.*?)(?<!\\)',?", aliases)]
                    exception_dict[(tvid, prodid)] = alias_list
                    del alias_list
                del url_data

    # XEM scene exceptions
    _xem_exceptions_fetcher()
    for xem_ex in xem_exception_dict:
        if xem_ex in exception_dict:
            exception_dict[xem_ex] = exception_dict[xem_ex] + xem_exception_dict[xem_ex]
        else:
            exception_dict[xem_ex] = xem_exception_dict[xem_ex]

    # AniDB scene exceptions
    _anidb_exceptions_fetcher()
    for anidb_ex in anidb_exception_dict:
        if anidb_ex in exception_dict:
            exception_dict[anidb_ex] = exception_dict[anidb_ex] + anidb_exception_dict[anidb_ex]
        else:
            exception_dict[anidb_ex] = anidb_exception_dict[anidb_ex]

    changed_exceptions = False

    # write all the exceptions we got off the net into the database
    my_db = db.DBConnection()
    cl = []
    for cur_tvid_prodid in exception_dict:

        # get a list of the existing exceptions for this ID
        existing_exceptions = [x['show_name'] for x in
                               my_db.select('SELECT show_name'
                                            ' FROM scene_exceptions'
                                            ' WHERE indexer = ? AND indexer_id = ?',
                                            list(cur_tvid_prodid))]

        if cur_tvid_prodid not in exception_dict:
            continue

        for cur_exception_dict in exception_dict[cur_tvid_prodid]:
            try:
                cur_exception, cur_season = next(iteritems(cur_exception_dict))
            except (BaseException, Exception):
                logger.log('scene exception error', logger.ERROR)
                logger.log(traceback.format_exc(), logger.ERROR)
                continue

            # if this exception isn't already in the DB then add it
            if cur_exception not in existing_exceptions:

                if PY2 and not isinstance(cur_exception, text_type):
                    cur_exception = text_type(cur_exception, 'utf-8', 'replace')

                cl.append(['INSERT INTO scene_exceptions'
                           ' (indexer, indexer_id, show_name, season) VALUES (?,?,?,?)',
                           list(cur_tvid_prodid) + [cur_exception, cur_season]])
                changed_exceptions = True

    if cl:
        my_db.mass_action(cl)

    # since this could invalidate the results of the cache we clear it out after updating
    if changed_exceptions:
        logger.log(u'Updated scene exceptions')
    else:
        logger.log(u'No scene exceptions update needed')

    # cleanup
    exception_dict.clear()
    anidb_exception_dict.clear()
    xem_exception_dict.clear()


def update_scene_exceptions(tvid, prodid, scene_exceptions):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    :param tvid: tvid
    :type tvid: int
    :param prodid: prodid
    :type prodid: int or long
    :param scene_exceptions:
    :type scene_exceptions: List
    """
    global exceptionsCache
    my_db = db.DBConnection()
    my_db.action('DELETE FROM scene_exceptions'
                 ' WHERE indexer = ? AND indexer_id = ?',
                 [tvid, prodid])

    # A change has been made to the scene exception list. Let's clear the cache, to make this visible
    exceptionsCache[(tvid, prodid)] = defaultdict(list)

    logger.log(u'Updating scene exceptions', logger.MESSAGE)
    for exception in scene_exceptions:
        cur_season, cur_exception = exception.split('|', 1)

        exceptionsCache[(tvid, prodid)][cur_season].append(cur_exception)

        if PY2 and not isinstance(cur_exception, text_type):
            cur_exception = text_type(cur_exception, 'utf-8', 'replace')

        my_db.action('INSERT INTO scene_exceptions'
                     ' (indexer, indexer_id, show_name, season) VALUES (?,?,?,?)',
                     [tvid, prodid, cur_exception, cur_season])


def _anidb_exceptions_fetcher():
    global anidb_exception_dict

    if should_refresh('anidb'):
        logger.log(u'Checking for AniDB scene exception updates')
        for cur_show_obj in filter_iter(lambda _s: _s.is_anime and TVINFO_TVDB == _s.tvid, sickbeard.showList):
            try:
                anime = create_anidb_obj(name=cur_show_obj.name, tvdbid=cur_show_obj.prodid, autoCorrectName=True)
            except (BaseException, Exception):
                continue
            if anime.name and anime.name != cur_show_obj.name:
                anidb_exception_dict[(cur_show_obj.tvid, cur_show_obj.prodid)] = [{anime.name: -1}]

        set_last_refresh('anidb')
    return anidb_exception_dict


def _xem_exceptions_fetcher():
    global xem_exception_dict

    xem_list = 'xem_us'
    for cur_show_obj in sickbeard.showList:
        if cur_show_obj.is_anime and not cur_show_obj.paused:
            xem_list = 'xem'
            break

    if should_refresh(xem_list):
        for tvid in [i for i in sickbeard.TVInfoAPI().sources if 'xem_origin' in sickbeard.TVInfoAPI(i).config]:
            logger.log(u'Checking for XEM scene exception updates for %s' % sickbeard.TVInfoAPI(tvid).name)

            url = 'http://thexem.de/map/allNames?origin=%s%s&seasonNumbers=1'\
                  % (sickbeard.TVInfoAPI(tvid).config['xem_origin'], ('&language=us', '')['xem' == xem_list])

            parsed_json = helpers.get_url(url, parse_json=True, timeout=90)
            if not parsed_json:
                logger.log(u'Check scene exceptions update failed for %s, Unable to get URL: %s'
                           % (sickbeard.TVInfoAPI(tvid).name, url), logger.ERROR)
                continue

            if 'failure' == parsed_json['result']:
                continue

            for prodid, names in iteritems(parsed_json['data']):
                try:
                    xem_exception_dict[(tvid, int(prodid))] = names
                except (BaseException, Exception):
                    continue

        set_last_refresh(xem_list)

    return xem_exception_dict


def _xem_get_ids(infosrc_name, xem_origin):
    """

    :param infosrc_name:
    :type infosrc_name: AnyStr
    :param xem_origin:
    :type xem_origin: AnyStr
    :return:
    :rtype: List
    """
    xem_ids = []

    url = 'http://thexem.de/map/havemap?origin=%s' % xem_origin

    task = 'Fetching show ids with%s xem scene mapping%s for origin'
    logger.log(u'%s %s' % (task % ('', 's'), infosrc_name))
    parsed_json = helpers.get_url(url, parse_json=True, timeout=90)
    if not isinstance(parsed_json, dict) or not parsed_json:
        logger.log(u'Failed %s %s, Unable to get URL: %s'
                   % (task.lower() % ('', 's'), infosrc_name, url), logger.ERROR)
    else:
        if 'success' == parsed_json.get('result', '') and 'data' in parsed_json:
            xem_ids = list(set(filter_iter(lambda prodid: 0 < prodid,
                                           map_iter(lambda pid: helpers.try_int(pid), parsed_json['data']))))
            if 0 == len(xem_ids):
                logger.log(u'Failed %s %s, no data items parsed from URL: %s'
                           % (task.lower() % ('', 's'), infosrc_name, url), logger.WARNING)

    logger.log(u'Finished %s %s' % (task.lower() % (' %s' % len(xem_ids), helpers.maybe_plural(xem_ids)),
                                    infosrc_name))
    return xem_ids


def get_xem_ids():
    global xem_ids_list

    for tvid, name in iteritems(sickbeard.TVInfoAPI().xem_supported_sources):
        xem_ids = _xem_get_ids(name, sickbeard.TVInfoAPI(tvid).config['xem_origin'])
        if len(xem_ids):
            xem_ids_list[tvid] = xem_ids


def has_abs_episodes(ep_obj=None, name=None):
    """

    :param ep_obj: episode object
    :type ep_obj: sickbeard.tv.TVEpisode or None
    :param name: name
    :type name: AnyStr
    :return:
    :rtype: bool
    """
    return any([(name or ep_obj.show_obj.name or '').lower().startswith(x.lower()) for x in [
        'The Eighties', 'The Making of the Mob', 'The Night Of', 'Roots 2016', 'Trepalium'
    ]])
