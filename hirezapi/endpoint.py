import aiohttp
import asyncio
from hashlib import md5
from datetime import datetime, timedelta

from .exceptions import Unauthorized

class Endpoint:
    
    def __init__(self, endpoint: str, dev_id: str, auth_key: str):
        self.endpoint = endpoint.rstrip('/')
        self._session_key = ""
        self._session_expires = datetime.utcnow()
        self._http_session = aiohttp.ClientSession(raise_for_status=True)
        self.__dev_id = dev_id
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
        return md5("".join([self.__dev_id, method_name, self.__auth_key, timestamp]).encode()).hexdigest()

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
        """
        method_name = method_name.lower()
        req_stack = [self.endpoint, "{}json".format(method_name)]
        
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
                # off by 1s because of a rare race condition
                self._session_expires = now + timedelta(minutes=14, seconds=59)
                req_stack.extend([self._session_key, timestamp])
        if data:
            req_stack.extend(map(str, data))
        
        req_url = '/'.join(req_stack)
        tries = 3
        for tries_left in reversed(range(tries)):
            try:
                async with self._http_session.get(req_url, timeout = 5) as response:
                    return await response.json()
            # For some reason, sometimes we get disconnected or timed out here.
            # If this happens, just give the api a short break and try again.
            except (aiohttp.ServerDisconnectedError, asyncio.TimeoutError) as exc:
                if not tries_left:
                    raise
                print("Got {}, retrying...".format(exc))
                await asyncio.sleep((tries - tries_left) * 0.5)

