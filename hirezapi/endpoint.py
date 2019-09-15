import aiohttp
import asyncio
from hashlib import md5
from typing import Union
from datetime import datetime, timedelta

from .exceptions import HTTPException, Unauthorized

# off by 10s because of a rare race condition
session_lifetime = timedelta(minutes=14, seconds=50)

class Endpoint:
    """
    Represents a basic Hi-Rez endpoint URL wrapper, for handling response types and session creation.
    
    Parameters
    ----------
    url : str
        The endpoint's base URL.
    dev_id : Union[int, str]
        Your developer's ID (devId).
    auth_key : str
        Your developer's authentication key (authKey).
    loop : Optional[asyncio.AbstractEventLoop]
        The loop you want to use for this Endpoint.
        Default loop is used when not provided.

    .. note:: You can request your developer ID and authorization key here:
        https://fs12.formsite.com/HiRez/form48/secure_index.html
    """
    def __init__(self, url: str, dev_id: Union[int, str], auth_key: str, *, loop: asyncio.AbstractEventLoop = None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.url = url.rstrip('/')
        self._session_key = ''
        self._session_expires = datetime.utcnow()
        self._http_session = aiohttp.ClientSession(raise_for_status=True, loop=loop)
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
        return md5(''.join([self.__dev_id, method_name, self.__auth_key, timestamp]).encode()).hexdigest()

    async def request(self, method_name: str, data: list = None):
        """
        Makes a direct request to the HiRez API.
        
        For methods available, see docs: https://docs.google.com/document/d/1OFS-3ocSx-1Rvg4afAnEHlT3917MAK_6eJTR6rzr-BM

        Parameters
        ----------
        method_name : str
            The name of the method requested. This shouldn't include the reponse type as it's
            added for you.
        data : Optional[List[Union[int, str]]]
            A list of method parameters requested to add at the end of the request, if applicable.
            Those should be either integers or strings.
        
        Returns
        -------
        Union[list, dict]
            A raw server's response as a list or a dictionary.
        
        Raises
        ------
        HTTPException
            Whenever it was impossible to fetch the data in a reliable manner.
            Check the `cause` attribute for the original exception that lead to this.
        """
        method_name = method_name.lower()
        req_stack = [self.url, "{}json".format(method_name)]
        
        tries = 3
        for tries_left in reversed(range(tries)):
            try:
                if method_name != "ping":
                    now = datetime.utcnow()
                    timestamp = now.strftime("%Y%m%d%H%M%S")
                    req_stack.extend([self.__dev_id, self._get_signature(method_name, timestamp)])
                    if method_name == "createsession":
                        req_stack.append(timestamp)
                    else:
                        if now >= self._session_expires:
                            session_response = await self.request("createsession") # recursion
                            session_id = session_response.get("session_id")
                            if not session_id:
                                raise Unauthorized
                            self._session_key = session_id
                        self._session_expires = now + session_lifetime
                        req_stack.extend([self._session_key, timestamp])
                if data:
                    req_stack.extend(map(str, data))
                
                req_url = '/'.join(req_stack)
        
                async with self._http_session.get(req_url, timeout = 5) as response:
                    # if response and "ret_msg" in response[0] and response[0]["ret_msg"]:
                    #     # we've got some Hi-Rez API error
                    #     pass # TODO: Maybe process this here?
                    return await response.json()
            
            # For some reason, sometimes we get disconnected or timed out here.
            # If this happens, just give the api a short break and try again.
            except (aiohttp.ServerDisconnectedError, asyncio.TimeoutError) as exc:
                if not tries_left: # no more breaks ¯\_(ツ)_/¯
                    raise HTTPException(exc)
                print("Got {}, retrying...".format(exc.__class__))
                await asyncio.sleep((tries - tries_left) * 0.5)
            # Some other exception happened, so just wrap it and propagate along
            except Exception as exc:
                raise HTTPException(exc)
        
        # we've run out of tries, so ¯\_(ツ)_/¯
        # we shouldn't ever end up here, this is a fail-safe
        raise HTTPException