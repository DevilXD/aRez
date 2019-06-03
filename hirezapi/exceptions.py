class Unauthorized(Exception):
    def __init__(self):
        super().__init__("Your authorization credentials are invalid!")

class Private(Exception):
    def __init__(self):
        super().__init__("This player profile is private!")