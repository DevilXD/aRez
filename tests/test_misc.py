from enum import IntEnum
from asyncio import Event, wait_for
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import arez
import pytest

from .conftest import MATCH


# test type errors
@pytest.mark.base()
@pytest.mark.asyncio()
async def test_type_errors(api: arez.PaladinsAPI, player: arez.Player):
    # cache.py
    # language not None or an instance of arez.Language
    with pytest.raises(TypeError):
        api.set_default_language("en")  # type: ignore

    # api.py
    # not a function or None
    with pytest.raises(TypeError):
        api.register_status_callback(0)  # type: ignore
    # not 1 or 2 input arguments
    with pytest.raises(ValueError):
        api.register_status_callback(lambda: 0)  # type: ignore
    # player not an int or str
    with pytest.raises(TypeError):
        await api.get_player([])  # type: ignore
    # no iterable
    with pytest.raises(TypeError):
        await api.get_players(0)  # type: ignore
    # iterable with not an int inside
    with pytest.raises(TypeError):
        await api.get_players(["test"])  # type: ignore
    # player_name not a str
    with pytest.raises(TypeError):
        await api.search_players(1234)  # type: ignore
    # platform not an instance of arez.Platform
    with pytest.raises(TypeError):
        await api.search_players("1234", "pc")  # type: ignore
    # platform_id not a str
    with pytest.raises(TypeError):
        await api.get_from_platform("1234", "pc")  # type: ignore
    # platform not None or an instance of arez.Platform
    with pytest.raises(TypeError):
        await api.get_from_platform(1234, "pc")  # type: ignore
    # match_id not an int
    with pytest.raises(TypeError):
        await api.get_match("1234")  # type: ignore
    # language not None or an instance of arez.Language
    with pytest.raises(TypeError):
        await api.get_match(1234, "en")  # type: ignore
    # no iterable
    with pytest.raises(TypeError):
        await api.get_matches(1234)  # type: ignore
    # iterable with not an int inside
    with pytest.raises(TypeError):
        await api.get_matches(["1234"])  # type: ignore
    # language not None or an instance of arez.Language
    with pytest.raises(TypeError):
        await api.get_matches([1234], "en")  # type: ignore
    # queue not an instance of arez.Queue
    start = end = datetime.utcnow()
    with pytest.raises(TypeError):
        ran = False
        async for match in api.get_matches_for_queue(
            "casual", start=start, end=end  # type: ignore
        ):
            ran = True
        assert not ran
    # language not None or an instance of arez.Language
    with pytest.raises(TypeError):
        ran = False
        async for match in api.get_matches_for_queue(
            arez.Queue.Casual_Siege, language="en", start=start, end=end  # type: ignore
        ):
            ran = True
        assert not ran

    # player.py
    # language not None or an instance of arez.Language
    with pytest.raises(TypeError):
        await player.get_loadouts("en")  # type: ignore
    # language not None or an instance of arez.Language
    with pytest.raises(TypeError):
        await player.get_champion_stats("en")  # type: ignore
    # language not None or an instance of arez.Language
    with pytest.raises(TypeError):
        await player.get_match_history("en")  # type: ignore


# test enum creation and casting
@pytest.mark.base()
@pytest.mark.dependency()
@pytest.mark.dependency(scope="session")
def test_enum_meta():
    if TYPE_CHECKING:
        class Enum(IntEnum):
            pass
    else:
        Enum = arez.enums.Enum

    class WithDefault(Enum, default_value=0):
        Unknown = 0
        NoSpace = 1
        With_Space = 2

    class NoDefault(Enum):
        One = 1
        Two = 2
        Three = 3

    e = WithDefault("nospace")  # fuzzy string member getting
    assert e is WithDefault.NoSpace  # identity and attribute access
    assert isinstance(e, WithDefault)  # isinstance
    assert str(e) == "NoSpace"  # str cast
    assert int(e) == 1  # int cast
    assert e == 1  # int comparison
    assert repr(e) == "<WithDefault.NoSpace: 1>"  # repr
    # same but with a space in the name
    e = WithDefault("with space")
    assert e is WithDefault.With_Space
    assert isinstance(e, WithDefault)
    assert str(e) == e.name == "With Space"
    assert int(e) == e.value == e == 2
    assert repr(e) == "<WithDefault.With_Space: 2>"
    # member acquisition by value
    e = WithDefault(1)
    assert e is WithDefault.NoSpace
    # Iteration
    for i, e in enumerate(WithDefault):
        assert i == e.value
    # None for unknown input
    e = WithDefault("1234")
    assert e is None
    # Default for unknown input
    e = WithDefault("1234", _return_default=True)
    assert e is WithDefault.Unknown
    # If no default value is set - return unchanged
    e = NoDefault("1234", _return_default=True)
    assert e == "1234"
    # Can't delete attributes
    with pytest.raises(AttributeError):
        del NoDefault.One
    assert hasattr(NoDefault, "One")
    # Can't reassign attributes
    with pytest.raises(AttributeError):
        NoDefault.Two = "test"
    assert isinstance(NoDefault.Two, NoDefault)
    # Can't assign other attributes
    with pytest.raises(AttributeError):
        NoDefault.test = "test"
    assert not hasattr(NoDefault, "test")
    # Can't create new members
    e = None
    with pytest.raises(TypeError):
        e = NoDefault("Four", 4)
    assert e is None
    assert not hasattr(NoDefault, "Four")


@pytest.mark.base()
@pytest.mark.dependency(depends=["test_enum_meta"])
@pytest.mark.dependency(scope="session")
def test_enum():
    # rank special aliases
    r = arez.Rank("bronze5")
    assert r is arez.Rank.Bronze_V
    # rank alt name
    assert r.alt_name == "Bronze 5"
    assert arez.Rank.Master.alt_name == "Master"
    # queue methods
    assert arez.Queue.Casual_Siege.is_casual()
    assert arez.Queue.Competitive_Keyboard.is_ranked()
    assert arez.Queue.Training_Siege.is_training()
    assert arez.Queue.Custom_Ascension_Peak.is_custom()
    assert arez.Queue.Casual_Siege.is_siege()
    assert arez.Queue.Onslaught.is_onslaught()
    assert arez.Queue.Team_Deathmatch.is_tdm()
    assert arez.Queue.Custom_Magistrates_Archives_KotH.is_koth()


@pytest.mark.api()
@pytest.mark.dependency()
def test_server_status_merge():
    cs = arez.status._convert_status
    colors = arez.statuspage.colors
    # prepare the table of possibilities and their results
    # colors:
    G = colors["green"]   # 2528092
    B = colors["blue"]    # 3447003
    Y = colors["yellow"]  # 16568108
    O = colors["orange"]  # 15234063
    R = colors["red"]     # 15158332
    cases = [
        ((True, False, "Operational",          G), (True, False, "Operational",          G)),
        ((True, False, "Maintenance",          B), (True, False, "Operational",          G)),
        ((True, False, "Degraded Performance", Y), (True, False, "Degraded Performance", Y)),
        ((True, False, "Partial Outage",       O), (True, False, "Operational",          G)),
        ((True, False, "Major Outage",         R), (True, False, "Operational",          G)),

        ((True, True, "Operational",          G), (True, True, "Limited Access", Y)),
        ((True, True, "Maintenance",          B), (True, True, "Maintenance",    B)),
        ((True, True, "Degraded Performance", Y), (True, True, "Limited Access", Y)),
        ((True, True, "Partial Outage",       O), (True, True, "Partial Outage", O)),
        ((True, True, "Major Outage",         R), (True, True, "Major Outage",   R)),

        ((False, False, "Operational",          G), (False, False, "Outage",         R)),
        ((False, False, "Maintenance",          B), (False, False, "Maintenance",    B)),
        ((False, False, "Degraded Performance", Y), (False, False, "Outage",         R)),
        ((False, False, "Partial Outage",       O), (False, False, "Partial Outage", O)),
        ((False, False, "Major Outage",         R), (False, False, "Major Outage",   R)),

        ((None, None, "Operational",          G), (True,  False, "Operational",          G)),
        ((None, None, "Maintenance",          B), (False, False, "Maintenance",          B)),
        ((None, None, "Degraded Performance", Y), (True,  False, "Degraded Performance", Y)),
        ((None, None, "Partial Outage",       O), (False, False, "Partial Outage",       O)),
        ((None, None, "Major Outage",         R), (False, False, "Major Outage",         R)),

        ((True,  False, None, None), (True,  False, "Operational",    G)),
        ((True,  True,  None, None), (True,  True,  "Limited Access", Y)),
        ((False, False, None, None), (False, False, "Outage",         R)),
    ]
    # test each case
    for inputs, outputs in cases:
        assert cs(*inputs) == outputs


@pytest.mark.api()
@pytest.mark.vcr()
@pytest.mark.slow()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["test_server_status_merge"])
@pytest.mark.dependency(depends=["tests/test_endpoint.py::test_session"], scope="session")
async def test_get_server_status(api: arez.PaladinsAPI):
    # empty responses from both
    with pytest.raises(arez.NotFound):
        current_status = await api.get_server_status(force_refresh=True)
    # empty api response, but statuspage returns
    current_status = await api.get_server_status(force_refresh=True)
    assert "epic" in current_status.statuses
    # api response but empty statuspage, not all up
    current_status = await api.get_server_status(force_refresh=True)
    assert "epic" not in current_status.statuses
    assert not current_status.all_up
    assert not current_status.limited_access
    # both available, all up but limited access
    current_status = await api.get_server_status(force_refresh=True)
    assert isinstance(current_status, arez.ServerStatus)
    assert current_status.all_up
    assert current_status.limited_access
    # test returning cached
    current_status2 = await api.get_server_status()
    assert current_status2 is current_status
    # test cached on empty responses from both
    current_status2 = await api.get_server_status(force_refresh=True)
    assert current_status2 is current_status
    # test attributes
    keys = ("pc", "ps4", "xbox", "switch", "epic", "pts")
    assert (
        len(keys) == len(current_status.statuses)
        and all(k in current_status.statuses for k in keys)
    )
    # repr
    repr(current_status)
    repr(current_status.statuses["pc"])

    # test callback loop
    n = 0
    can_continue = Event()
    half_second = timedelta(seconds=0.5)

    async def test_callback(callback, *, double_register=False):
        nonlocal n
        n = 0
        can_continue.clear()
        api.register_status_callback(callback, half_second, half_second)
        if double_register:
            api.register_status_callback(callback, half_second, half_second)
        await wait_for(can_continue.wait(), timeout=2)
        api.register_status_callback(None)

    # normal function, one argument
    def callback(after):
        nonlocal n
        n += 1
        if n >= 2:  # count two calls
            can_continue.set()
    # double register
    await test_callback(callback, double_register=True)

    # normal function, two arguments
    def callback(before, after):  # type: ignore[no-redef]
        nonlocal n
        assert before != after
        n += 1
        if n >= 2:  # count two calls
            can_continue.set()
    await test_callback(callback)
    # double un-register
    api.register_status_callback(None)

    # async function, one argument
    async def callback(after):  # type: ignore[no-redef]
        nonlocal n
        n += 1
        if n >= 2:  # count two calls
            can_continue.set()
    await test_callback(callback)

    # async function, two arguments
    async def callback(before, after):  # type: ignore[no-redef]
        nonlocal n
        assert before != after
        n += 1
        if n >= 2:  # count two calls
            can_continue.set()
    await test_callback(callback)


@pytest.mark.api()
@pytest.mark.vcr()
@pytest.mark.base()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["test_enum"])
@pytest.mark.dependency(depends=["tests/test_endpoint.py::test_session"], scope="session")
async def test_cache(api: arez.PaladinsAPI):
    # set default language
    api.set_default_language(arez.Language.English)
    # fail initialize
    result = await api.initialize()
    assert result is False
    # proper initialize
    result = await api.initialize(language=arez.Language.English)
    assert result is True
    # getting entry
    entry = api.get_entry()
    assert isinstance(entry, arez.CacheEntry)
    # repr
    repr(entry)
    # get a valid champion, then an invalid card and talent
    champion = entry.champions.get("Androxus")
    assert champion is not None
    # repr Champion and Ability
    repr(champion)
    repr(list(champion.abilities)[0])
    # test Skins
    skins = await champion.get_skins()
    assert len(skins) > 0, f"No skins returned for {champion.name}!"
    assert all(isinstance(s, arez.Skin) for s in skins)
    # Skin repr
    repr(skins[0])
    # get specific entry - fail cos missing initialize
    german = arez.Language.German
    entry = api.get_entry(german)
    assert entry is None


@pytest.mark.api()
@pytest.mark.vcr()
@pytest.mark.base()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["test_cache"])
@pytest.mark.dependency(
    depends=[
        "tests/test_api.py::test_bounty",
        "tests/test_api.py::test_get_match",
        "tests/test_match.py::test_live_match",
        "tests/test_player.py::test_player_history",
        "tests/test_player.py::test_player_loadouts",
        "tests/test_player.py::test_player_champion_stats",
    ],
    scope="session",
)
async def test_cache_disabled(api: arez.PaladinsAPI, player: arez.Player):
    # temporarly disable the cache, and make sure no cached entry exists
    api.cache_enabled = False  # disable cache
    if arez.Language.English in api._cache:
        del api._cache[arez.Language.English]  # delete cache

    try:
        # test get_match
        match = await api.get_match(MATCH)
        assert isinstance(next(match.players).champion, arez.CacheObject)
        # test live players
        status = await player.get_status()
        live_match = await status.get_live_match()
        assert live_match is not None
        assert isinstance(next(live_match.players).champion, arez.CacheObject)
        # test player history
        history = await player.get_match_history()
        if len(history) > 0:
            partial_match = history[0]
            assert isinstance(partial_match.champion, arez.CacheObject)
            # repr CacheObject
            repr(partial_match)
            # MatchItem and LoadoutCard descriptions (empty strings)
            if len(partial_match.items) > 0:
                partial_match.items[0].description()
            if len(partial_match.loadout.cards) > 0:
                partial_match.loadout.cards[0].description()
        # test player loadouts
        loadouts = await player.get_loadouts()
        assert isinstance(loadouts[0].champion, arez.CacheObject)
        # test player champion stats
        stats_list = await player.get_champion_stats()
        assert isinstance(stats_list[0].champion, arez.CacheObject)
        # test bounty store
        bounty_items = await api.get_bounty()
        assert isinstance(bounty_items[0].champion, arez.CacheObject)
    finally:
        # finalize
        player._api.cache_enabled = True  # enable cache back
        await api.initialize()  # re-fetch the entry


@pytest.mark.api()
@pytest.mark.vcr()
@pytest.mark.base()
@pytest.mark.match()
@pytest.mark.player()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["test_cache"])
@pytest.mark.dependency(depends=["tests/test_player.py::test_player_history"], scope="session")
async def test_comparisons(
    api: arez.PaladinsAPI, player: arez.PartialPlayer, private_player: arez.PartialPlayer
):
    o1 = arez.CacheObject()
    o2 = arez.CacheObject(id=1)
    o3 = arez.CacheObject(name="Test")
    assert o1 == o1
    assert o2 == o2
    assert o3 == o3
    assert o1 != o2
    assert o2 != o3
    # players
    assert player != private_player
    assert player != None  # noqa
    # champions
    entry = api.get_entry()
    assert entry is not None
    champions = list(entry.champions)
    assert champions[0] != champions[1]
    assert champions[0] != None  # noqa
    # devices
    devices = list(entry.devices)
    assert devices[0] != devices[1]
    assert devices[0] != None  # noqa

    items = cards = []  # solely to silence the linter about those being possibly unbound
    history = await player.get_match_history()
    # loop because the last match might have only one item/card in it
    for partial_match in history:
        items = partial_match.items
        cards = partial_match.loadout.cards
        if len(items) >= 2 and len(cards) >= 2:
            break
    # match item
    assert items[0] != items[1]
    # NotImplemented
    assert items[0] != None  # noqa
    # loadout card
    assert cards[0] != cards[1]
    # NotImplemented
    assert cards[0] != None  # noqa


@pytest.mark.api()
@pytest.mark.vcr()
@pytest.mark.base()
@pytest.mark.player()
@pytest.mark.asyncio()
async def test_hashable(
    api: arez.PaladinsAPI, player: arez.PartialPlayer, private_player: arez.PartialPlayer
):
    # Champion, Device, Ability
    entry = api.get_entry()
    assert entry is not None
    hash(entry.champions[0])
    hash(entry.champions[0])  # hash again for a cache hit
    hash(entry.abilities[0])
    hash(entry.devices[0])
    # Loadout
    loadouts = await player.get_loadouts()
    hash(loadouts[0])
    # Player and PartialPlayer
    hash(player)
    hash(player)  # hash again for a cache hit
    hash(private_player)


@pytest.mark.vcr()
@pytest.mark.player()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["tests/test_player.py::test_player_expand"], scope="session")
async def test_player_ranked_best(player: arez.PartialPlayer):
    player1 = await player
    assert isinstance(player1.ranked_best, arez.RankedStats)
    player2 = await player
    assert isinstance(player2.ranked_best, arez.RankedStats)
