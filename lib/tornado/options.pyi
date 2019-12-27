# Stubs for tornado_py3.options (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Set, TextIO, Tuple

class Error(Exception): ...

class OptionParser:
    def __init__(self) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
    def __iter__(self) -> Iterator: ...
    def __contains__(self, name: str) -> bool: ...
    def __getitem__(self, name: str) -> Any: ...
    def __setitem__(self, name: str, value: Any) -> None: ...
    def items(self) -> Iterable[Tuple[str, Any]]: ...
    def groups(self) -> Set[str]: ...
    def group_dict(self, group: str) -> Dict[str, Any]: ...
    def as_dict(self) -> Dict[str, Any]: ...
    def define(self, name: str, default: Any=..., type: Optional[type]=..., help: Optional[str]=..., metavar: Optional[str]=..., multiple: bool=..., group: Optional[str]=..., callback: Optional[Callable[[Any], None]]=...) -> None: ...
    def parse_command_line(self, args: Optional[List[str]]=..., final: bool=...) -> List[str]: ...
    def parse_config_file(self, path: str, final: bool=...) -> None: ...
    def print_help(self, file: Optional[TextIO]=...) -> None: ...
    def add_parse_callback(self, callback: Callable[[], None]) -> None: ...
    def run_parse_callbacks(self) -> None: ...
    def mockable(self) -> _Mockable: ...

class _Mockable:
    def __init__(self, options: OptionParser) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
    def __delattr__(self, name: str) -> None: ...

class _Option:
    UNSET: Any = ...
    name: Any = ...
    type: Any = ...
    help: Any = ...
    metavar: Any = ...
    multiple: Any = ...
    file_name: Any = ...
    group_name: Any = ...
    callback: Any = ...
    default: Any = ...
    def __init__(self, name: str, default: Any=..., type: Optional[type]=..., help: Optional[str]=..., metavar: Optional[str]=..., multiple: bool=..., file_name: Optional[str]=..., group_name: Optional[str]=..., callback: Optional[Callable[[Any], None]]=...) -> None: ...
    def value(self) -> Any: ...
    def parse(self, value: str) -> Any: ...
    def set(self, value: Any) -> None: ...

options: Any

def define(name: str, default: Any=..., type: Optional[type]=..., help: Optional[str]=..., metavar: Optional[str]=..., multiple: bool=..., group: Optional[str]=..., callback: Optional[Callable[[Any], None]]=...) -> None: ...
def parse_command_line(args: Optional[List[str]]=..., final: bool=...) -> List[str]: ...
def parse_config_file(path: str, final: bool=...) -> None: ...
def print_help(file: Optional[TextIO]=...) -> None: ...
def add_parse_callback(callback: Callable[[], None]) -> None: ...
