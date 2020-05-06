import arez
import pytest


pytestmark = [
    pytest.mark.vcr,
    pytest.mark.player,
    pytest.mark.asyncio,
    pytest.mark.dependency(
        depends=["tests/test_misc.py::test_enum", "tests/test_endpoint.py::test_session"],
        scope="session"
    )
]


async def test_player_expand(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    player = await player
    assert isinstance(player, arez.Player)
    # 0 ID private
    with pytest.raises(arez.Private):
        player = await private_player
    # invalid
    with pytest.raises(arez.NotFound):
        player = await invalid_player
    # no privacy flag private
    with pytest.raises(arez.Private):
        player = await no_flag_private_player


async def test_player_status(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    status = await player.get_status()
    assert status is not None
    # private
    with pytest.raises(arez.Private):
        status = await private_player.get_status()
    # invalid
    status = await invalid_player.get_status()
    assert status is None
    # no privacy flag private
    status = await no_flag_private_player.get_status()
    assert status is None


async def test_player_friends(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    friends = await player.get_friends()
    assert all(isinstance(f, arez.PartialPlayer) for f in friends)
    # private
    with pytest.raises(arez.Private):
        friends = await private_player.get_friends()
    # invalid
    friends = await invalid_player.get_friends()
    assert len(friends) == 0
    # no privacy flag private
    friends = await no_flag_private_player.get_friends()
    assert len(friends) == 0


async def test_player_loadouts(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    loadouts = await player.get_loadouts()
    assert all(isinstance(l, arez.Loadout) for l in loadouts)
    # private
    with pytest.raises(arez.Private):
        loadouts = await private_player.get_loadouts()
    # invalid
    loadouts = await invalid_player.get_loadouts()
    assert len(loadouts) == 0
    # no privacy flag private
    loadouts = await no_flag_private_player.get_loadouts()
    assert len(loadouts) == 0


async def test_player_champion_stats(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    stats = await player.get_champion_stats()
    assert all(isinstance(l, arez.ChampionStats) for l in stats)
    # private
    with pytest.raises(arez.Private):
        stats = await private_player.get_champion_stats()
    # invalid
    stats = await invalid_player.get_champion_stats()
    assert len(stats) == 0
    # no privacy flag private
    stats = await invalid_player.get_champion_stats()
    assert len(stats) == 0


async def test_player_match_history(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    history = await player.get_match_history()
    assert all(isinstance(match, arez.PartialMatch) for match in history)
    # private
    with pytest.raises(arez.Private):
        history = await private_player.get_match_history()
    # invalid
    history = await invalid_player.get_match_history()
    assert len(history) == 0
    # no privacy flag private
    history = await invalid_player.get_match_history()
    assert len(history) == 0
