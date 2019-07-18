class HTTPException(Exception):
    """
    General exception raised by the Endpoint in cases where getting a response from the server wasn't possible.
    
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

class Unauthorized(Exception):
    def __init__(self):
        super().__init__("Your authorization credentials are invalid!")

class Private(Exception):
    def __init__(self):
        super().__init__("This player profile is private!")