from __future__ import annotations

import aiohttp
import asyncio
import logging
from hashlib import md5
from random import gauss
from typing import Optional, Union
from datetime import datetime, timedelta

from .exceptions import HTTPException, Unauthorized, Unavailable


__all__ = ["Endpoint"]
session_lifetime = timedelta(minutes=15)
timeout = aiohttp.ClientTimeout(total=20, connect=5)
logger = logging.getLogger(__package__)


class Endpoint:
    """
    Represents a basic Hi-Rez endpoint URL wrapper, for handling response types and
    session creation.

    .. note::

        You can request your developer ID and authorization key `here.
        <https://fs12.formsite.com/HiRez/form48/secure_index.html>`_

    .. warning::

        The main API and data cache classes use this class as base, so all of it's methods
        are already available there. This class is listed here solely for documentation purposes.
        Instanting it yourself is possible, but not recommended.

    Parameters
    ----------
    url : str
        The endpoint's base URL.
    dev_id : Union[int, str]
        Your developer's ID (devId).
    auth_key : str
        Your developer's authentication key (authKey).
    loop : Optional[asyncio.AbstractEventLoop]
        The event loop you want to use for this Endpoint.\n
        Default loop is used when not provided.
    """
    def __init__(
        self,
        url: str,
        dev_id: Union[int, str],
        auth_key: str,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        if loop is None:  # pragma: no cover
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.url = url.rstrip('/')
        self._session_key = ''
        self._session_lock = asyncio.Lock()
        self._session_expires = datetime.utcnow()
        self._http_session = aiohttp.ClientSession(timeout=timeout, loop=loop)
        self.__dev_id = str(dev_id)
        self.__auth_key = auth_key.upper()

    def __del__(self):
        self._http_session.detach()

    async def close(self):
        """
        Closes the underlying API connection.

        Attempting to make a request after the connection is closed
        will result in a `RuntimeError`.
        """
        await self._http_session.close()  # pragma: no cover

    async def __aenter__(self) -> Endpoint:  # pragma: no cover
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        await self._http_session.close()

    def _get_signature(self, method_name: str, timestamp: str):
        return md5(''.join((
            self.__dev_id, method_name, self.__auth_key, timestamp
        )).encode()).hexdigest()

    async def request(self, method_name: str, *data: Union[int, str]):
        """
        Makes a direct request to the HiRez API.

        For all methods available (and their parameters), `please see Hi-Rez API docs.
        <https://docs.google.com/document/d/1OFS-3ocSx-1Rvg4afAnEHlT3917MAK_6eJTR6rzr-BM>`_

        Parameters
        ----------
        method_name : str
            The name of the method requested. This shouldn't include the reponse type as it's
            added for you.
        *data : Union[int, str]
            Method parameters requested to add at the end of the request, if applicable.
            Those should be either integers or strings.

        Returns
        -------
        Union[list, dict]
            A raw server's response as a list or a dictionary.

        Raises
        ------
        HTTPException
            Whenever it was impossible to fetch the data in a reliable manner.\n
            Check the `HTTPException.cause` attribute for the original exception (and reason)
            that lead to this.
        Unauthorized
            When the developer's ID (devId) or the developer's authentication key (authKey)
            are deemed invalid.
        Unavailable
            When the Hi-Rez API switches to emergency mode, and no data could be returned
            at this time.
        """
        last_exc = None
        method_name = method_name.lower()

        for tries in range(5):  # pragma: no branch
            try:
                req_stack = [self.url, f"{method_name}json"]
                if method_name == "createsession":
                    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    req_stack.extend(
                        (self.__dev_id, self._get_signature(method_name, timestamp), timestamp)
                    )
                elif method_name != "ping":
                    async with self._session_lock:
                        now = datetime.utcnow()
                        if now >= self._session_expires:
                            session_response = await self.request("createsession")  # recursion
                            session_id = session_response.get("session_id")
                            if not session_id:
                                raise Unauthorized
                            self._session_key = session_id
                        self._session_expires = now + session_lifetime
                    # reacquire the current time
                    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    req_stack.extend((
                        self.__dev_id,
                        self._get_signature(method_name, timestamp),
                        self._session_key,
                        timestamp,
                    ))
                if data:
                    req_stack.extend(map(str, data))

                req_url = '/'.join(req_stack)
                logger.debug(f"endpoint.request: {method_name}: {req_url}")

                async with self._http_session.get(req_url) as response:
                    # Handle special HTTP status codes
                    if response.status == 503:
                        # '503: Service Unavailable'
                        raise Unavailable
                    else:
                        # Raise for any other error code
                        response.raise_for_status()

                    res_data: Union[list, dict] = await response.json()

                    if res_data:
                        if isinstance(res_data, list) and isinstance(res_data[0], dict):
                            error = res_data[0].get("ret_msg")
                        elif isinstance(res_data, dict):
                            error = res_data.get("ret_msg")
                        else:
                            error = None
                        if error:
                            # we've got some Hi-Rez API error, handle some of them here

                            # Invalid session
                            if error == "Invalid session id.":
                                # Invalidate the current session by expiring it, then retry
                                self._session_expires = datetime.utcnow()
                                continue

                    return res_data

            # When connection problems happen, just give the api a short break and try again.
            except (
                aiohttp.ClientConnectionError, asyncio.TimeoutError
            ) as exc:  # pragma: no cover
                last_exc = exc  # store for the last iteration raise
                if isinstance(exc, asyncio.TimeoutError):
                    logger.warning("Timed out, retrying...")
                elif isinstance(exc, aiohttp.ServerDisconnectedError):
                    logger.warning("Server disconnected, retrying...")
                else:
                    logger.warning("Connection problems, retrying...")
                # pass and retry on the next loop
            # When '.raise_for_status()' generates this one, just wrap it and raise
            except aiohttp.ClientResponseError as exc:
                logger.exception("Got a response error")
                raise HTTPException(exc)
            # For the case where 'createsession' raises it recursively,
            # or the Hi-Rez API is down - just pass it along
            except (Unauthorized, Unavailable) as exc:
                if isinstance(exc, Unauthorized):
                    logger.error("You are Unauthorized")
                elif isinstance(exc, Unavailable):  # pragma: no branch
                    logger.warning("Hi-Rez API is Unavailable")
                raise
            # Some other exception happened, so just wrap it and propagate along
            except Exception as exc:
                logger.exception("Got an unexpected exception")
                raise HTTPException(exc)

            # Sleep before retrying
            await asyncio.sleep(tries * 0.5 * gauss(1, 0.1))  # pragma: no cover

        # we've run out of tries, so ¯\_(ツ)_/¯
        # we shouldn't ever end up here, this is a fail-safe
        logger.error("Ran out of retries", exc_info=last_exc)  # pragma: no cover
        raise HTTPException(last_exc)  # pragma: no cover
