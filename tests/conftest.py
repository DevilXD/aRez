import re
import asyncio
import warnings
from datetime import datetime
from typing import Optional, List, Dict
from collections import defaultdict, deque, namedtuple

import arez
import pytest
from vcr import VCR
from pytest import Module, Item

from .secret import DEV_ID, AUTH_KEY


pytest_plugins = ["asyncio", "recording", "dependency"]

#####################
# testing constants #
#####################

# base datetime - has to be within the last 30 days
BASE_DATETIME = datetime(2020, 4, 27, 0, 0)

# match IDs - no private players
MATCH         = 969680571  # Siege or Onslaught
MATCH_TDM     = 973464436  # TDM
INVALID_MATCH = 1234       # invalid

# named tuple for player data storage
test_player = namedtuple("test_player", ("name", "id", "platform"))

# not private player, PC platform
PLAYER = test_player("DevilXD", 5959045, 5)
# not private player, console platform
CONSOLE_PLAYER = test_player("Djinscar", 501140683, 9)
# private player, any platform
PRIVATE_PLAYER = test_player("FenixSpider", 13307488, 1)
# invalid player
INVALID_PLAYER = test_player("42", 1234, 1)

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
    # this manages the closing of the API after tests as well
    async with arez.PaladinsAPI(DEV_ID, AUTH_KEY, initialize=True) as api:
        yield api


# wrap a normal player
@pytest.fixture(scope="session")
def player(api: arez.PaladinsAPI):
    return api.wrap_player(PLAYER.id)


# wrap a 0 ID private player
@pytest.fixture(scope="session")
def private_player(api: arez.PaladinsAPI):
    return api.wrap_player(0)


# wrap an invalid player
@pytest.fixture(scope="session")
def invalid_player(api: arez.PaladinsAPI):
    return api.wrap_player(INVALID_PLAYER.id)


# wrap a private player without flag
@pytest.fixture(scope="session")
def no_flag_private_player(api: arez.PaladinsAPI):
    return api.wrap_player(PRIVATE_PLAYER.id)


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


# special hook to make pytest-dependency support reordering based on deps
def pytest_collection_modifyitems(items: List[Item]):
    session_names: List[str] = []
    module_names: Dict[Module, List[str]] = defaultdict(list)

    # gather dependency names
    for item in items:
        for marker in item.iter_markers("dependency"):
            scope = marker.kwargs.get("scope", "module")
            if scope == "module":
                module_names[item.module].append(item.name)
            elif scope == "session":
                session_names.append(item.nodeid)  # use 'nodeid' instead of the name

    final_items: List[Item] = []
    session_deps: Dict[str, Item] = {}
    module_deps: Dict[Module, Dict[str, Item]] = defaultdict(dict)

    # group the dependencies by their scopes
    deque_items = deque(items)
    while deque_items:
        item = deque_items.popleft()
        correct_order: Optional[bool] = True
        for marker in item.iter_markers("dependency"):
            depends = marker.kwargs.get("depends", [])
            scope = marker.kwargs.get("scope", "module")
            # pick a scope
            if scope == "module":
                scope_deps = module_deps[item.module]
                scope_names = module_names[item.module]
            elif scope == "session":
                scope_deps = session_deps
                scope_names = session_names
            # check deps
            if not all(d in scope_deps for d in depends):
                # check to see if we're ever gonna see a dep like that
                for d in depends:
                    if d in scope_names:
                        if correct_order is not None:
                            correct_order = False
                    else:
                        correct_order = None
                        warnings.warn(
                            f"Dependency '{d}' of '{item.nodeid}' doesn't exist, "
                            "or has incorrect scope!",
                            RuntimeWarning,
                        )
                break
            # save
            if scope == "module":
                module_deps[item.module][item.name] = item
            elif scope == "session":
                session_deps[item.nodeid] = item  # use 'nodeid' instead of the name
        # 'correct_order' possible values:
        # None  - invalid dependency, add anyway
        # True  - add it to the final list
        # False - missing dependency, add it back to the processing deque
        if correct_order is None:
            # TODO: Take the config into account here
            final_items.append(item)
        elif correct_order:
            final_items.append(item)
        else:
            deque_items.append(item)

    assert len(items) == len(final_items) and all(i in items for i in final_items)
    items[:] = final_items
