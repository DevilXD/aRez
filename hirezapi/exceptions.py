class HiRezAPIException(Exception):
    """
    The base exception type for this entire package.
    """
    pass

class HTTPException(HiRezAPIException):
    """
    General exception raised by the Endpoint in cases where getting a response from the server wasn't possible.
    
    Inherits from `HiRezAPIException`.

    Attributes
    ----------
    cause : Optional[Exception]
        The original exception cause. This is usually:
        - aiohttp.ClientResponseError or it's derivatives
        - asyncio.TimeoutError when the request times out
        - Unauthorized exception when your credentials were invalid
        - None if the cause was unknown
    """
    def __init__(self, original_exc = None):
        super().__init__("There was an error while processing the request!")
        self.cause = original_exc

class Unauthorized(HiRezAPIException):
    """
    The exception raised when the developer's ID and authorization key provided were deemed
    invalid, and the API was unable to estabilish a session because of it.

    Inherits from `HiRezAPIException`.
    """
    def __init__(self):
        super().__init__("Your authorization credentials are invalid!")

class Private(HiRezAPIException):
    """
    The exception raised when trying to fetch information about a private player's profile.

    Inherits from `HiRezAPIException`.
    """
    def __init__(self):
        super().__init__("This player profile is private!")