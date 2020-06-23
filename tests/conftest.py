from __future__ import annotations

import re
import asyncio
import warnings
from datetime import datetime
from collections import deque, namedtuple
from typing import Optional, List, Dict, Set, TypedDict, Literal

import arez
import pytest
from vcr import VCR
from pytest import Module, Item

from .secret import DEV_ID, AUTH_KEY


pytest_plugins = ["asyncio", "recording", "dependency"]

#####################
# testing constants #
#####################

# base datetime - has to be within the last 30 days, date only
BASE_DATETIME = datetime(2020, 6, 3)

# match IDs - at least one private player
MATCH         = 987998836  # Siege or Onslaught
MATCH_TDM     = 987401201  # TDM
INVALID_MATCH = 1234       # invalid

# named tuple for player data storage
test_player = namedtuple("test_player", ("id", "name", "platform"))

# not private player, PC platform
PLAYER = test_player(5959045, "DevilXD", 5)
# not private player, console platform
CONSOLE_PLAYER = test_player(501140683, "Djinscar", 9)
# private player, any platform
PRIVATE_PLAYER = test_player(13307488, "FenixSpider", 1)
# old player, any platform
# low lever, created long time ago, some data might be missing:
# • creation date
# • last login date
# • Region
OLD_PLAYER = test_player(733658, "Endeavor", 1)
# invalid player
INVALID_PLAYER = test_player(1234, "42", 1)

# named tuple for platform testing
test_platform = namedtuple("test_platform", ("platform_id", "platform"))
# valid
PLATFORM_PLAYER = test_platform(157205897611968514, 25)
# invalid
INVALID_PLATFORM = test_platform(1234, 25)


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


# generates an API instance
@pytest.fixture(scope="session")
async def api():
    # this manages the closing after tests as well
    async with arez.PaladinsAPI(DEV_ID, AUTH_KEY) as api:
        yield api


# generates a status page instance
@pytest.fixture(scope="session")
async def sp():
    # this manages the closing after tests as well
    async with arez.StatusPage("http://status.hirezstudios.com/") as page:
        yield page


# wrap a normal player
@pytest.fixture(scope="session")
def player(api: arez.PaladinsAPI):
    return api.wrap_player(*PLAYER)


# wrap a 0 ID private player
@pytest.fixture(scope="session")
def private_player(api: arez.PaladinsAPI):
    return api.wrap_player(0)


# wrap an old player
@pytest.fixture(scope="session")
def old_player(api: arez.PaladinsAPI):
    return api.wrap_player(*OLD_PLAYER)


# wrap an invalid player
@pytest.fixture(scope="session")
def invalid_player(api: arez.PaladinsAPI):
    return api.wrap_player(*INVALID_PLAYER)


# wrap a private player without flag
@pytest.fixture(scope="session")
def no_flag_private_player(api: arez.PaladinsAPI):
    return api.wrap_player(*PRIVATE_PLAYER)


def filter_request(request):
    if request.host == "api.paladins.com":
        # remove the authentication part
        request.uri = re.sub(
            r'([a-z]+json)/\d{1,5}/[0-9a-f]+/(?:[0-9A-F]+/)?[0-9]{14}',
            r'\1',
            request.uri,
            flags=re.I,
        )
    return request


def filter_response(response):
    response["url"] = ''  # hide the URL
    return response


@pytest.fixture(scope="session")
def vcr_config():
    return {
        "record_mode": "new_episodes",  # "once",
        "cassette_library_dir": "tests/cassettes",
        "path_transformer": VCR.ensure_suffix(".yaml"),
        "before_record_request": filter_request,
        "before_record_response": filter_response,
    }


# Everything below is related to pytest-dependency changing the order of the tests so that
# they execute in the order dictated by dependencies itself, without skipping tests if
# the dependency is only found to be collected later. It can be removed once this gets merged
# as base functionality - ref: https://github.com/RKrahl/pytest-dependency/pull/44

Scope = Literal["module", "session"]


class ManagerDict(TypedDict):
    session: Optional[OrderManager]
    module: Dict[Module, OrderManager]


class OrderManager:

    managers = ManagerDict({
        "session": None,
        "module": {},
    })

    def __init__(self):
        self.names: Set[str] = set()
        self.dependencies: Dict[str, Item] = {}

    @classmethod
    def get_for_scope(cls, item: Item, scope: Scope) -> OrderManager:
        if scope == "session":
            session_manager = cls.managers["session"]
            if session_manager is None:
                session_manager = cls.managers["session"] = cls()
            return session_manager
        # module scope
        module = item.module
        module_managers = cls.managers["module"]
        if module not in module_managers:
            module_managers[module] = cls()
        return module_managers[module]

    def check_dependencies(self, dependency_list: List[str], name: str) -> bool:
        if not all(d in self.dependencies for d in dependency_list):
            # check to see if we're ever gonna see a dep like that
            for d in dependency_list:
                if d not in self.names:
                    warnings.warn(
                        f"Dependency '{d}' of '{name}' doesn't exist, "
                        "or has incorrect scope!",
                        RuntimeWarning,
                    )
            return False
        return True

    def register_name(self, name: str):
        self.names.add(name)

    def add_dependency(self, item: Item, name: str):
        self.dependencies[name] = item


def remove_parametrization(item: Item, scope: Scope) -> str:
    nodeid = item.nodeid.replace("::()::", "::")
    if scope == "session" or scope == "package":
        name = nodeid
    elif scope == "module":
        name = nodeid.split("::", 1)[1]
    elif scope == "class":
        name = nodeid.split("::", 2)[2]

    original = item.originalname if item.originalname is not None else item.name
    # remove the parametrization part at the end
    if not name.endswith(original):
        index = name.rindex(original) + len(original)
        name = name[:index]
    return name


# special hook to make pytest-dependency support reordering based on deps
def pytest_collection_modifyitems(items: List[Item]):
    # gather dependency names
    for item in items:
        for marker in item.iter_markers("dependency"):
            scope = marker.kwargs.get("scope", "module")
            name = marker.kwargs.get("name")
            if not name:
                name = remove_parametrization(item, scope)

            manager = OrderManager.get_for_scope(item, scope)
            manager.register_name(name)

    final_items: List[Item] = []

    # group the dependencies by their scopes
    cycles = 0
    deque_items = deque(items)
    while deque_items:
        if cycles >= len(deque_items):
            # seems like we're stuck in a loop now
            # just add the remaining items and finish up
            final_items.extend(deque_items)
            break
        item = deque_items.popleft()
        for marker in item.iter_markers("dependency"):
            depends = marker.kwargs.get("depends", [])
            scope = marker.kwargs.get("scope", "module")
            name = marker.kwargs.get("name")
            if not name:
                name = remove_parametrization(item, scope)

            manager = OrderManager.get_for_scope(item, scope)
            if manager.check_dependencies(depends, name):
                manager.add_dependency(item, name)
            else:
                deque_items.append(item)
                cycles += 1
                break
        else:
            # runs only when the for loop wasn't broken out of
            final_items.append(item)
            cycles = 0

    assert len(items) == len(final_items) and all(i in items for i in final_items)
    items[:] = final_items
