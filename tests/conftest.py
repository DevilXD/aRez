from __future__ import annotations

import re
import asyncio
from typing import Literal
from datetime import datetime
from collections import namedtuple

import arez
import pytest
from vcr import VCR
from pytest import Item

from .secret import DEV_ID, AUTH_KEY

######################
# Note to maintaners #
######################

# To properly test the library, you'll need to specify your own secret.py file, containing
# two variables: DEV_ID and AUTH_KEY. Those are your API access credentials of course.
# The testing suite will generate and store cassette files, allowing you to redo the tests as many
# times as you'd want to, and everything should work as long as you manually update
# these constants below:

# BASE_DATETIME
# MATCH
# MATCH_TDM

# Once the cassette files are generated, you won't need to touch these ever again,
# unless you expect the API to change the data types it returns (keys were added or removed).
# Make sure to read the notes for each constant you update, as they may specify additional
# restrictions, without which you won't achieve 100% coverage.

pytest_plugins = ["asyncio", "recording", "pytest_cov", "pytest_order"]

#####################
# Testing constants #
#####################

# base datetime - has to be within the last 3-30 days, date only
BASE_DATETIME = datetime(2021, 2, 15)

# match IDs - at least one private player
MATCH         = 1065720250  # Ranked Siege
MATCH_TDM     = 1066210958  # TDM
INVALID_MATCH = 1234        # invalid

# named tuple for player data storage
test_player = namedtuple("test_player", ("id", "name", "platform"))

# not private player, PC platform
PLAYER = test_player(5959045, "DevilX3", 5)
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


Scope = Literal["module", "session"]


def remove_parametrization(item: Item, scope: Scope) -> str:
    nodeid = item.nodeid.replace("::()::", "::")
    if scope == "session" or scope == "package":
        name = nodeid
    elif scope == "module":
        name = nodeid.split("::", 1)[1]
    elif scope == "class":
        name = nodeid.split("::", 2)[2]

    # originalname is added as an attribute, somehow
    original = item.originalname if item.originalname is not None else item.name  # type: ignore
    # remove the parametrization part at the end
    if not name.endswith(original):
        index = name.rindex(original) + len(original)
        name = name[:index]
    return name
