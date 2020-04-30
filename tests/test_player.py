import arez
import pytest


pytestmark = [
    pytest.mark.vcr,
    pytest.mark.asyncio,
    pytest.mark.dependency(
        depends=["tests/test_misc.py::test_enum", "tests/test_endpoint.py::test_session"],
        scope="session"
    )
]


async def test_player_expand(api_player: arez.PartialPlayer):
    player = await api_player
    assert isinstance(player, arez.Player)
    assert isinstance(player.ranked_best, arez.RankedStats)


async def test_player_status(api_player: arez.PartialPlayer):
    status = await api_player.get_status()
    assert status is not None


@pytest.mark.xfail()  # we can live without testing the live match
async def test_player_live_match(api_player: arez.PartialPlayer):
    status = await api_player.get_status()
    assert status is not None
    live_match = await status.get_live_match(expand_players=True)
    assert isinstance(live_match, arez.LiveMatch)
    assert all(isinstance(p.player, arez.Player) or p.player.private for p in live_match.players)


async def test_player_friends(api_player: arez.PartialPlayer):
    friends = await api_player.get_friends()
    assert all(isinstance(f, arez.PartialPlayer) for f in friends)


async def test_player_loadouts(api_player: arez.PartialPlayer):
    loadouts = await api_player.get_loadouts()
    assert all(isinstance(l, arez.Loadout) for l in loadouts)


async def test_player_champion_stats(api_player: arez.PartialPlayer):
    stats = await api_player.get_champion_stats()
    assert all(isinstance(l, arez.ChampionStats) for l in stats)


async def test_player_match_history(api_player: arez.PartialPlayer):
    history = await api_player.get_match_history()
    assert all(isinstance(match, arez.PartialMatch) for match in history)
