import asyncio
from datetime import datetime, timedelta

import arez
import pytest
import aiohttp


pytestmark = [pytest.mark.vcr, pytest.mark.base, pytest.mark.asyncio]


# test network timeouts and disconnects
@pytest.mark.dependency()
async def test_stability(api: arez.PaladinsAPI):
    # test timeout error
    coro = api.request("ping")
    task = asyncio.create_task(coro)
    await asyncio.sleep(0.1)
    try:
        coro.throw(asyncio.TimeoutError)
        await task
    except (RuntimeError, OSError):
        pass
    # test disconnected error
    coro = api.request("ping")
    task = asyncio.create_task(coro)
    await asyncio.sleep(0.1)
    try:
        coro.throw(aiohttp.ServerDisconnectedError)
        await task
    except (RuntimeError, OSError):
        pass


# test ping
@pytest.mark.dependency(depends=["test_stability"])
async def test_ping(api: arez.PaladinsAPI):
    await api.request("ping")


@pytest.mark.dependency(depends=["test_ping"])
async def test_unauthorized(api: arez.PaladinsAPI):
    # temporarly overwrite the authorization key with a fake one
    real_key = api._Endpoint__auth_key  # type: ignore
    api._Endpoint__auth_key = "FAKE_KEY"  # type: ignore
    try:
        with pytest.raises(arez.Unauthorized):
            await api.request("testsession")
    finally:
        api._Endpoint__auth_key = real_key  # type: ignore


# test session creation
@pytest.mark.dependency(depends=["test_ping"])
@pytest.mark.dependency(scope="session")
async def test_session(api: arez.PaladinsAPI):
    # test invalid session
    api._session_key = "ABCDEF"
    api._session_expires = datetime.utcnow() + timedelta(seconds=30)
    await api.request("getpatchinfo")
    api._session_expires = datetime.utcnow() - timedelta(seconds=30)
    # test normal session
    await api.request("testsession")


# test unexpected exception
@pytest.mark.dependency(depends=["test_session"])
async def test_unexpected(api: arez.PaladinsAPI):
    with pytest.raises(arez.HTTPException):
        await api.request("unexpected")


# test error handling
@pytest.mark.dependency(depends=["test_session"])
async def test_404(api: arez.PaladinsAPI):
    with pytest.raises(arez.HTTPException):
        await api.request("nonexistent_endpoint")


# test unavailable
@pytest.mark.dependency(depends=["test_session"])
async def test_503(api: arez.PaladinsAPI):
    with pytest.raises(arez.Unavailable):
        await api.request("unavailable")
