from copy import copy

import arez
import pytest

from .conftest import MATCH, INVALID_MATCH


pytestmark = [
    pytest.mark.vcr,
    pytest.mark.match,
    pytest.mark.asyncio,
    pytest.mark.order(after=["test_misc.py::test_enum", "test_misc.py::test_cache"])
]


@pytest.mark.order(after="test_player.py::test_player_history")
async def test_match_expand(player: arez.PartialPlayer):
    # fetch the history here
    history = await player.get_match_history()
    partial_match: arez.PartialMatch = history[0]
    # make an invalid match out of a valid partial one, by corrupting it's ID
    invalid_match = copy(partial_match)
    invalid_match.id = INVALID_MATCH

    # invalid
    with pytest.raises(arez.NotFound):
        match = await invalid_match
    # standard
    match = await partial_match
    assert isinstance(match, arez.Match)
    # verify that the data is consistent between partial and full matches
    match_attrs = [
        "queue", "region", "timestamp", "duration", "map_name", "winning_team",
    ]
    for attr in match_attrs:
        assert getattr(partial_match, attr) == getattr(match, attr)
    # verify the score - special case
    assert set(partial_match.score) == set(match.score)
    # verify the match player
    mp = arez.utils.get(match.players, player__id=player.id)
    assert isinstance(mp, arez.MatchPlayer)
    player_attrs = [
        "champion", "credits", "damage_done", "damage_bot", "damage_taken", "damage_mitigated",
        "healing_done", "healing_bot", "healing_self", "objective_time", "multikill_max",
        "team_number", "team_score", "winner",
    ]
    for attr in player_attrs:
        assert getattr(partial_match, attr) == getattr(mp, attr)
    # verify items
    for partial_item, mp_item in zip(partial_match.items, mp.items):
        assert partial_item == mp_item
    # verify loadout
    partial_loadout = partial_match.loadout
    mp_loadout = mp.loadout
    assert partial_loadout.talent == mp_loadout.talent
    for partial_card, mp_card in zip(partial_loadout.cards, mp_loadout.cards):
        assert partial_card == mp_card


@pytest.mark.order(after=[
    "test_api.py::test_get_match",
    "test_player.py::test_player_history",
])
async def test_match_disconnected(api: arez.PaladinsAPI, player: arez.PartialPlayer):
    # fetch the history here
    history = await player.get_match_history()
    partial_match = history[0]
    # get a normal match
    match = await api.get_match(MATCH)

    # check for disconnected
    assert not partial_match.disconnected
    assert all(not mp.disconnected for mp in match.players)


@pytest.mark.order(after="test_player.py::test_player_status")
async def test_live_match(player: arez.PartialPlayer):
    # no live match
    status = await player.get_status()
    assert isinstance(status, arez.PlayerStatus)
    assert status.queue is None
    assert status.live_match_id is None
    assert status.status != arez.Activity.In_Match
    # try fetching anyway
    live_match = await status.get_live_match()
    assert live_match is None
    # with live match
    status = await player.get_status()
    assert isinstance(status, arez.PlayerStatus)
    assert isinstance(status.queue, arez.Queue)
    assert isinstance(status.live_match_id, int)
    assert status.status == arez.Activity.In_Match
    # empty response
    live_match = await status.get_live_match()
    assert live_match is None
    # unsupported queue
    live_match = await status.get_live_match()
    assert live_match is None
    # standard
    live_match = await status.get_live_match()
    assert isinstance(live_match, arez.LiveMatch)
    assert all(isinstance(lp.player, arez.PartialPlayer) for lp in live_match.players)
    # repr LiveMatch and LivePlayer
    repr(live_match)
    if len(live_match.team1) + len(live_match.team2) > 0:
        repr(list(live_match.players)[0])
    # expand players after fetch
    await live_match.expand_players()
    assert all(
        isinstance(lp.player, arez.Player) or lp.player.private for lp in live_match.players
    )
    # expand players on fetch, specific language
    live_match = await status.get_live_match(language=arez.Language.English, expand_players=True)
    assert isinstance(live_match, arez.LiveMatch)
    assert all(
        isinstance(lp.player, arez.Player) or lp.player.private for lp in live_match.players
    )
