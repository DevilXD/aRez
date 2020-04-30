import pytest


# test session creation
@pytest.mark.vcr()
@pytest.mark.asyncio()
@pytest.mark.dependency(scope="session")
async def test_session(api):
    await api.request("testsession")
