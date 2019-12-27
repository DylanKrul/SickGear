# Stubs for tornado_py3.auth (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from tornado_py3 import httpclient
from typing import Any, Dict, List, Optional

class AuthError(Exception): ...

class OpenIdMixin:
    def authenticate_redirect(self, callback_uri: Optional[str]=..., ax_attrs: List[str]=...) -> None: ...
    async def get_authenticated_user(self, http_client: Optional[httpclient.AsyncHTTPClient]=...) -> Dict[str, Any]: ...
    def get_auth_http_client(self) -> httpclient.AsyncHTTPClient: ...

class OAuthMixin:
    async def authorize_redirect(self, callback_uri: Optional[str]=..., extra_params: Optional[Dict[str, Any]]=..., http_client: Optional[httpclient.AsyncHTTPClient]=...) -> None: ...
    async def get_authenticated_user(self, http_client: Optional[httpclient.AsyncHTTPClient]=...) -> Dict[str, Any]: ...
    def get_auth_http_client(self) -> httpclient.AsyncHTTPClient: ...

class OAuth2Mixin:
    def authorize_redirect(self, redirect_uri: Optional[str]=..., client_id: Optional[str]=..., client_secret: Optional[str]=..., extra_params: Optional[Dict[str, Any]]=..., scope: Optional[str]=..., response_type: str=...) -> None: ...
    async def oauth2_request(self, url: str, access_token: Optional[str]=..., post_args: Optional[Dict[str, Any]]=..., **args: Any) -> Any: ...
    def get_auth_http_client(self) -> httpclient.AsyncHTTPClient: ...

class TwitterMixin(OAuthMixin):
    async def authenticate_redirect(self, callback_uri: Optional[str]=...) -> None: ...
    async def twitter_request(self, path: str, access_token: Dict[str, Any], post_args: Optional[Dict[str, Any]]=..., **args: Any) -> Any: ...

class GoogleOAuth2Mixin(OAuth2Mixin):
    async def get_authenticated_user(self, redirect_uri: str, code: str) -> Dict[str, Any]: ...

class FacebookGraphMixin(OAuth2Mixin):
    async def get_authenticated_user(self, redirect_uri: str, client_id: str, client_secret: str, code: str, extra_fields: Optional[Dict[str, Any]]=...) -> Optional[Dict[str, Any]]: ...
    async def facebook_request(self, path: str, access_token: Optional[str]=..., post_args: Optional[Dict[str, Any]]=..., **args: Any) -> Any: ...
