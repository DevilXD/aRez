from datetime import datetime, timedelta

import arez
import pytest


pytestmark = [pytest.mark.vcr, pytest.mark.base, pytest.mark.asyncio]


# test ping
async def test_ping(api: arez.PaladinsAPI):
    await api.request("ping")


@pytest.mark.order(after="test_ping")
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
@pytest.mark.order(after="test_ping")
async def test_session(api: arez.PaladinsAPI):
    # test invalid session
    api._session_key = "ABCDEF"
    api._session_expires = datetime.utcnow() + timedelta(seconds=30)
    await api.request("getpatchinfo")
    api._session_expires = datetime.utcnow() - timedelta(seconds=30)
    # test normal session
    await api.request("testsession")
    # test explicit session
    response = await api.request("testsession", api._session_key)
    assert api._session_key in response


# test unexpected exception
@pytest.mark.order(after="test_session")
async def test_unexpected(api: arez.PaladinsAPI):
    with pytest.raises(arez.HTTPException):
        await api.request("unexpected")  # type: ignore[call-overload]


# test error handling
@pytest.mark.order(after="test_session")
async def test_404(api: arez.PaladinsAPI):
    with pytest.raises(arez.HTTPException):
        await api.request("nonexistent_endpoint")  # type: ignore[call-overload]


# test unavailable
@pytest.mark.order(after="test_session")
async def test_503(api: arez.PaladinsAPI):
    with pytest.raises(arez.Unavailable):
        await api.request("unavailable")  # type: ignore[call-overload]


# test limit reached
@pytest.mark.order(after="test_session")
async def test_limit_reached(api: arez.PaladinsAPI):
    with pytest.raises(arez.LimitReached):
        await api.request("limitreached")  # type: ignore[call-overload]
