import arez
import pytest


# test enum creation and casting
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


@pytest.mark.vcr()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["tests/test_endpoint.py::test_session"], scope="session")
async def test_get_server_status(api: arez.PaladinsAPI):
    current_status = await api.get_server_status(True)
    assert current_status is not None
    assert len(current_status.statuses) == 5
