from datetime import datetime

import arez
import pytest


pytestmark = [
    pytest.mark.vcr,
    pytest.mark.asyncio,
    pytest.mark.dependency(
        depends=["tests/test_misc.py::test_enum", "tests/test_endpoint.py::test_session"],
        scope="session",
    )
]


@pytest.mark.dependency(depends=["tests/utils/test_lookup.py::test_lookup"], scope="session")
async def test_champion_info(api_langs: arez.PaladinsAPI):
    champion_info = await api_langs.get_champion_info()
    assert champion_info is not None
    champion_count = len(champion_info.champions)
    # verify all 3 device categories separately
    assert len(champion_info.items) == 4 * 4, "Missing shop items!"
    try:
        assert len(champion_info.cards) == champion_count * 16, "Missing cards!"
    except AssertionError:
        # there is a chance only one champion is missing those - narrow it down
        if len(champion_info.cards) != (champion_count - 1) * 16:
            raise
        # lets see who is it
        for champion in champion_info.champions:
            assert champion.cards, f"Champion {champion.name} is missing cards!"
    try:
        assert len(champion_info.talents) == champion_count * 3, "Missing talents!"
    except AssertionError:
        if len(champion_info.talents) != (champion_count - 1) * 3:
            raise
        for champion in champion_info.champions:
            assert champion.talents, f"Champion {champion.name} is missing talents!"
    # verify we have all devices:
    # • 16 cards per champion
    # • 3 talents per champion
    # 4 categories of 4 shop items
    assert len(champion_info.devices) == champion_count * (16 + 3) + 4 * 4, "Missing devices!"
    # verify all champions are valid
    assert all(c for c in champion_info.champions), "Not all champions appear to be valid!"


async def test_get_player(api: arez.PaladinsAPI):
    player = await api.get_player("DevilXD")
    assert isinstance(player, arez.Player)


async def test_get_players(api: arez.PaladinsAPI):
    player_list = await api.get_players([5959045, 479353], return_private=True)
    assert len(player_list) > 0


async def test_search_players(api: arez.PaladinsAPI):
    steam = arez.Platform.Steam
    player_list = await api.search_players("DevilXD", steam)
    assert player_list and all(isinstance(p, arez.PartialPlayer) for p in player_list)


async def test_get_from_platform(api: arez.PaladinsAPI):
    discord = arez.Platform.Discord
    player = await api.get_from_platform(157205897611968514, discord)
    assert isinstance(player, arez.PartialPlayer)


async def test_get_match(api: arez.PaladinsAPI):
    match = await api.get_match(969680571, expand_players=True)
    assert isinstance(match, arez.Match)
    assert all(isinstance(p.player, arez.Player) for p in match.players)


async def test_get_matches(api: arez.PaladinsAPI):
    match_list = await api.get_matches([969680571, 969690571], expand_players=True)
    for match in match_list:
        assert isinstance(match, arez.Match)
        assert all(isinstance(p.player, arez.Player) for p in match.players)


async def test_get_matches_for_queue(api: arez.PaladinsAPI):
    queue = arez.Queue("casual")
    start = datetime(2020, 4, 27, 0, 0)
    end = datetime(2020, 4, 27, 0, 10)
    match_list = []
    async for match in api.get_matches_for_queue(queue, start=start, end=end, expand_players=True):
        match_list.append(match)
        if len(match_list) >= 10:
            break
    assert all(
        isinstance(p.player, arez.Player) or p.player.private
        for match in match_list
        for p in match.players
    )
