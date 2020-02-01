from typing import Optional


class ArezException(Exception):
    """
    The base exception type for this entire package.
    """
    pass


class HTTPException(ArezException):
    """
    General exception raised by the Endpoint in cases where getting a response from
    the server wasn't possible.

    Inherits from `ArezException`.

    Attributes
    ----------
    cause : Optional[Exception]
        The original exception cause. This is usually:\n
        • `aiohttp.ClientResponseError` or it's subclasses.\n
        • `asyncio.TimeoutError` when the request times out.\n
        • `Unauthorized` exception when your credentials were invalid.\n
        • `None` if the cause was unknown.
    """
    def __init__(self, original_exc: Optional[Exception] = None):
        super().__init__(
            "There was an error while processing the request: {!r}".format(original_exc)
        )
        self.cause = original_exc


class Unauthorized(ArezException):
    """
    The exception raised when the developer's ID and authorization key provided were deemed
    invalid, and the API was unable to estabilish a session because of it.

    Inherits from `ArezException`.
    """
    def __init__(self):
        super().__init__("Your authorization credentials are invalid!")


class Private(ArezException):
    """
    The exception raised when trying to fetch information about a private player's profile.

    Inherits from `ArezException`.
    """
    def __init__(self):
        super().__init__("This player profile is private!")
