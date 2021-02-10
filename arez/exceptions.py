from typing import Optional


__all__ = [
    "ArezException",
    "HTTPException",
    "Private",
    "NotFound",
    "Unauthorized",
    "Unavailable",
]


class ArezException(Exception):
    """
    The base exception type for this entire package.
    """
    pass


class HTTPException(ArezException):
    """
    General exception raised by the `Endpoint` in cases where getting a response from
    the server wasn't possible.

    Inherits from `ArezException`.

    Attributes
    ----------
    cause : Optional[Exception]
        The original exception cause. This is usually:\n
        • `aiohttp.ClientResponseError` when the request results in an unhandled HTTP error.\n
        • `aiohttp.ClientConnectionError` when the request couldn't complete \
        due to connection problems.\n
        • `asyncio.TimeoutError` when the request times out.\n
        • `TypeError` or `ValueError`, in rare cases when the API is having some internal error.\n
        • `None` if the cause was unknown.
    description : str
        A more detailed description of the error. This is usually an empty string,
        set only when the API is having some internal error.
    """
    def __init__(self, original_exc: Optional[Exception] = None, description: str = ''):
        if description:
            text = f"There was an error while processing the request: {description}"
        else:
            text = f"There was an error while processing the request!"
        text += f"\nCause: {original_exc!r}"
        super().__init__(text)
        self.cause = original_exc
        self.description = description


class Private(ArezException):
    """
    The exception raised when trying to fetch information about a private player's profile.

    Inherits from `ArezException`.
    """
    def __init__(self):
        super().__init__("This player profile is private!")


# Currently inherits from the base exception, might change to the 'HTTPException' in the future
class NotFound(ArezException):
    """
    The exception raised when trying to fetch information returned an empty response.

    Inherits from `ArezException`.
    """
    def __init__(self, name: str = "Data"):
        super().__init__(f"{name} not found!")


class Unauthorized(ArezException):
    """
    The exception raised when the developer's ID and authorization key provided were deemed
    invalid, and the API was unable to estabilish a session because of it.

    Inherits from `ArezException`.
    """
    def __init__(self):
        super().__init__("Your authorization credentials are invalid!")


class Unavailable(ArezException):
    """
    The exception raised when the Hi-Rez API is switched into emergency mode,
    returning ``503: Service Unavailable`` HTTP status code on all endpoints / methods,
    except the server status one. Generally means the API is currently down.

    Inherits from `ArezException`.
    """
    def __init__(self):
        super().__init__("Hi-Rez API is currently down!")
