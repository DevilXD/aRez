import arez
import pytest


# test ping
@pytest.mark.vcr()
@pytest.mark.base()
@pytest.mark.asyncio()
@pytest.mark.dependency()
async def test_ping(api):
    await api.request("ping")


# test session creation
@pytest.mark.vcr()
@pytest.mark.base()
@pytest.mark.asyncio()
@pytest.mark.dependency("test_ping")
@pytest.mark.dependency(scope="session")
async def test_session(api):
    await api.request("testsession")


# test error handling
@pytest.mark.vcr()
@pytest.mark.base()
@pytest.mark.asyncio()
async def test_404(api):
    with pytest.raises(arez.HTTPException):
        await api.request("nonexistent_endpoint")


# test unavailable
@pytest.mark.vcr()
@pytest.mark.base()
@pytest.mark.asyncio()
async def test_503(api):
    with pytest.raises(arez.Unavailable):
        await api.request("unavailable")
