import arez
import pytest


# test enum creation and casting
@pytest.mark.base()
@pytest.mark.dependency()
@pytest.mark.dependency(scope="session")
def test_enum():
    p = arez.Platform("steam")
    assert p is arez.Platform.Steam
    assert str(p) == "Steam"
    assert int(p) == 5
    l = arez.Language(2)
    assert l is arez.Language.German
    r = arez.Region("1234")
    assert r is None
    r = arez.Region("1234", return_default=True)
    assert r is arez.Region.Unknown


@pytest.mark.api()
@pytest.mark.vcr()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["tests/test_endpoint.py::test_session"], scope="session")
async def test_get_server_status(api: arez.PaladinsAPI):
    # test None
    current_status = await api.get_server_status()
    assert current_status is None
    # test fetching new
    current_status = await api.get_server_status(force_refresh=True)
    assert current_status is not None
    # test returning cached
    current_status2 = await api.get_server_status()
    assert current_status2 is current_status
    assert len(current_status.statuses) == 5


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
    result = await api.initialize()
    assert result is True
    # getting entry
    entry = api.get_entry()
    assert isinstance(entry, arez.CacheEntry)
    # fail getting a champion, talent, card, shop item and device, due to invalid ID
    assert api.get_champion(0) is None
    assert api.get_talent(0) is None
    assert api.get_card(0) is None
    assert api.get_item(0) is None
    assert api.get_device(0) is None
    # get specific entry - fail cos missing initialize
    german = arez.Language.German
    entry = api.get_entry(german)
    assert entry is None
    # fail getting a champion, talent, card, shop item and device, due to missing cache
    assert api.get_champion(0, language=german) is None
    assert api.get_talent(0, language=german) is None
    assert api.get_card(0, language=german) is None
    assert api.get_item(0, language=german) is None
    assert api.get_device(0, language=german) is None


@pytest.mark.player()
@pytest.mark.dependency(depends=["test_cache"])
def test_comparisons(
    api: arez.PaladinsAPI, player: arez.PartialPlayer, private_player: arez.PartialPlayer
):
    # players
    assert player != private_player
    # champions
    entry = api.get_entry()
    assert entry is not None
    champions = list(entry.champions)
    assert champions[0] != champions[1]
    # devices
    devices = list(entry.devices)
    assert devices[0] != devices[1]


@pytest.mark.vcr()
@pytest.mark.player()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["tests/test_player.py::test_player_expand"], scope="session")
async def test_player_ranked_best(player: arez.PartialPlayer):
    player1 = await player
    assert isinstance(player1.ranked_best, arez.RankedStats)
    player2 = await player
    assert isinstance(player2.ranked_best, arez.RankedStats)
