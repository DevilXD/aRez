import aiohttp
import asyncio
from hashlib import md5
from random import gauss
from typing import Union
from datetime import datetime, timedelta

from .exceptions import HTTPException, Unauthorized

session_lifetime = timedelta(minutes=15)
timeout = aiohttp.ClientTimeout(total=5)


class Endpoint:
    """
    Represents a basic Hi-Rez endpoint URL wrapper, for handling response types and
    session creation.

    Parameters
    ----------
    url : str
        The endpoint's base URL.
    dev_id : Union[int, str]
        Your developer's ID (devId).
    auth_key : str
        Your developer's authentication key (authKey).

    .. note:: You can request your developer ID and authorization key here:
        https://fs12.formsite.com/HiRez/form48/secure_index.html
    """
    def __init__(self, url: str, dev_id: Union[int, str], auth_key: str):
        loop = asyncio.get_running_loop()
        self.url = url.rstrip('/')
        self._session_key = ''
        self._session_expires = datetime.utcnow()
        self._http_session = aiohttp.ClientSession(
            raise_for_status=True, timeout=timeout, loop=loop
        )
        self.__dev_id = str(dev_id)
        self.__auth_key = auth_key.upper()

    def __del__(self):
        self._http_session.detach()

    async def close(self):
        """
        Closes the underlying API connection.

        Attempting to make a request after the connection is closed will result in a RuntimeError.
        """
        await self._http_session.close()

    async def __aenter__(self):
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

        For methods available, see docs:
        https://docs.google.com/document/d/1OFS-3ocSx-1Rvg4afAnEHlT3917MAK_6eJTR6rzr-BM

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
            Check the ``cause`` attribute for the original exception that lead to this.
        """
        method_name = method_name.lower()

        last_exc = None
        for tries in range(5):
            try:
                now = datetime.utcnow()
                req_stack = [self.url, "{}json".format(method_name)]
                if method_name != "ping":
                    timestamp = now.strftime("%Y%m%d%H%M%S")
                    req_stack.extend((self.__dev_id, self._get_signature(method_name, timestamp)))
                    if method_name == "createsession":
                        req_stack.append(timestamp)
                    else:
                        if now >= self._session_expires:
                            session_response = await self.request("createsession")  # recursion
                            session_id = session_response.get("session_id")
                            if not session_id:
                                raise Unauthorized
                            self._session_key = session_id
                        self._session_expires = now + session_lifetime
                        req_stack.extend((self._session_key, timestamp))
                if data:
                    req_stack.extend(map(str, data))

                req_url = '/'.join(req_stack)

                async with self._http_session.get(req_url) as response:
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
                                # Invalidate the current session by expiring it
                                self._session_expires = now
                                continue  # retry

                    return res_data

            # For some reason, sometimes we get disconnected or timed out here.
            # If this happens, just give the api a short break and try again.
            except (aiohttp.ServerDisconnectedError, asyncio.TimeoutError) as exc:
                last_exc = exc  # store for the last iteration raise
                if isinstance(exc, aiohttp.ServerDisconnectedError):
                    print("Server disconnected, retrying...")
                elif isinstance(exc, asyncio.TimeoutError):
                    print("Timed out, retrying...")
                else:
                    print("Unknown error, retrying...")
                await asyncio.sleep(tries * 0.5 * gauss(1, 0.1))
            # For the case where 'createsession' raises this - just pass it along
            except HTTPException:
                raise
            # Some other exception happened, so just wrap it and propagate along
            except Exception as exc:
                raise HTTPException(exc)

        # we've run out of tries, so ¯\_(ツ)_/¯
        # we shouldn't ever end up here, this is a fail-safe
        raise HTTPException(last_exc)
