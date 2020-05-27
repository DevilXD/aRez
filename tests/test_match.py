from copy import copy

import arez
import pytest

from .conftest import MATCH, INVALID_MATCH


pytestmark = [
    pytest.mark.vcr,
    pytest.mark.match,
    pytest.mark.asyncio,
    pytest.mark.dependency(
        depends=["tests/test_misc.py::test_enum", "tests/test_endpoint.py::test_session"],
        scope="session",
    )
]


@pytest.mark.dependency(depends=["tests/test_player.py::test_player_history"], scope="session")
async def test_match_expand(player: arez.PartialPlayer):
    # fetch the history here
    history = await player.get_match_history()
    partial_match = history[0]
    # make an invalid match out of a valid partial one, by corrupting it's ID
    invalid_match = copy(partial_match)
    invalid_match.id = INVALID_MATCH

    # standard
    match = await partial_match
    assert isinstance(match, arez.Match)
    # invalid
    with pytest.raises(arez.NotFound):
        match = await invalid_match


@pytest.mark.dependency(
    depends=[
        "tests/test_api.py::test_get_match",
        "tests/test_player.py::test_player_history",
    ],
    scope="session",
)
async def test_match_disconnected(api: arez.PaladinsAPI, player: arez.PartialPlayer):
    # fetch the history here
    history = await player.get_match_history()
    partial_match = history[0]
    # get a normal match
    match = await api.get_match(MATCH)

    # check for disconnected
    assert not partial_match.disconnected
    assert all(not mp.disconnected for mp in match.players)


@pytest.mark.dependency(depends=["tests/test_player.py::test_player_status"], scope="session")
async def test_live_match(player: arez.PartialPlayer):
    status = await player.get_status()
    assert status is not None
    # standard
    live_match = await status.get_live_match()
    assert isinstance(live_match, arez.LiveMatch)
    assert all(isinstance(lp.player, arez.PartialPlayer) for lp in live_match.players)
    # expand players after fetch
    await live_match.expand_players()
    assert all(
        isinstance(lp.player, arez.Player) or lp.player.private for lp in live_match.players
    )
    # expand players on fetch
    live_match = await status.get_live_match(expand_players=True)
    assert isinstance(live_match, arez.LiveMatch)
    assert all(
        isinstance(lp.player, arez.Player) or lp.player.private for lp in live_match.players
    )
