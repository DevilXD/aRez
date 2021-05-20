import arez
import pytest


pytestmark = [
    pytest.mark.vcr,
    pytest.mark.player,
    pytest.mark.asyncio,
    pytest.mark.order(after=["test_misc.py::test_enum", "test_misc.py::test_cache"])
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
    # repr
    repr(status)
    # private
    with pytest.raises(arez.Private):
        status = await private_player.get_status()
    # invalid
    with pytest.raises(arez.NotFound):
        status = await invalid_player.get_status()
    # no privacy flag private
    with pytest.raises(arez.NotFound):
        status = await no_flag_private_player.get_status()


async def test_player_friends(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    friends = await player.get_friends()
    assert len(friends) > 0 and all(isinstance(f, arez.PartialPlayer) for f in friends)
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
    loadouts_lookup = await player.get_loadouts()
    assert all(isinstance(l, arez.Loadout) for l in loadouts_lookup)
    # get per champion
    loadouts_list = loadouts_lookup.get("Androxus")
    assert (
        isinstance(loadouts_list, list)
        and all(isinstance(l, arez.Loadout) for l in loadouts_list)
    )
    # fuzzy
    loadouts_list = loadouts_lookup.get_fuzzy("andro")
    assert (
        isinstance(loadouts_list, list)
        and all(isinstance(l, arez.Loadout) for l in loadouts_list)
    )
    # repr of a loadout and a loadout card
    if len(loadouts_lookup) > 0:
        loadout = loadouts_lookup[0]
        repr(loadout)
        if loadout.cards:
            repr(loadout.cards[0])
    # private
    with pytest.raises(arez.Private):
        loadouts_lookup = await private_player.get_loadouts()
    # invalid + explicit language
    loadouts_lookup = await invalid_player.get_loadouts(language=arez.Language.English)
    assert len(loadouts_lookup) == 0
    # no privacy flag private
    loadouts_lookup = await no_flag_private_player.get_loadouts()
    assert len(loadouts_lookup) == 0


async def test_player_champion_stats(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    stats_lookup = await player.get_champion_stats()
    assert all(isinstance(l, arez.ChampionStats) for l in stats_lookup)
    # repr
    if len(stats_lookup) > 0:
        stats1 = stats_lookup[0]
        repr(stats1)
        # WinLose and KDA mixin properties
        stats1.df
        stats1.kda
        stats1.kda2
        stats1.kda_text
        stats1.winrate_text
    # get per champion
    stats2 = stats_lookup.get("Androxus")
    assert isinstance(stats2, arez.ChampionStats)
    # fuzzy
    stats2 = stats_lookup.get_fuzzy("andro")
    assert isinstance(stats2, arez.ChampionStats)
    # queue filtered
    stats_lookup = await player.get_champion_stats(queue=arez.Queue.Casual_Siege)
    assert all(isinstance(l, arez.ChampionStats) for l in stats_lookup)
    # private
    with pytest.raises(arez.Private):
        stats_lookup = await private_player.get_champion_stats()
    # invalid + explicit language
    stats_lookup = await invalid_player.get_champion_stats(language=arez.Language.English)
    assert len(stats_lookup) == 0
    # no privacy flag private
    stats_lookup = await no_flag_private_player.get_champion_stats()
    assert len(stats_lookup) == 0


async def test_player_history(
    player: arez.PartialPlayer,
    private_player: arez.PartialPlayer,
    invalid_player: arez.PartialPlayer,
    no_flag_private_player: arez.PartialPlayer,
):
    # standard
    history = await player.get_match_history()
    assert all(isinstance(match, arez.PartialMatch) for match in history)
    # repr PartialMatch, MatchItem and MatchLoadout
    for match in history:
        repr(match)  # PartialMatch
        repr(match.loadout)  # MatchLoadout
        if not match.loadout.cards:
            continue
        match.loadout.cards[0].description()  # LoadoutCard description
        assert match.shielding == match.damage_mitigated  # shielding property
        if len(match.items) > 0:
            repr(match.items[0])  # MatchItem
            match.items[0].description()
            break
    # private
    with pytest.raises(arez.Private):
        history = await private_player.get_match_history()
    # invalid + explicit language
    history = await invalid_player.get_match_history(language=arez.Language.English)
    assert len(history) == 0
    # no privacy flag private
    history = await no_flag_private_player.get_match_history()
    assert len(history) == 0


@pytest.mark.vcr()
@pytest.mark.player()
@pytest.mark.asyncio()
@pytest.mark.order(after="test_player_expand")
async def test_player_dynamic_attributes(player: arez.PartialPlayer):
    # test ranked_best
    player1 = await player
    player2 = await player
    assert isinstance(player1.ranked_best, arez.RankedStats)
    assert isinstance(player2.ranked_best, arez.RankedStats)
    # test calculated_level
    assert player1.calculated_level == 10
    assert player2.calculated_level == 683
