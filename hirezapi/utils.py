from enum import Enum
from datetime import datetime, timedelta
from operator import attrgetter
from typing import Union, Optional, Iterable, AsyncGenerator

from .enumerations import Activity, Queue

def convert_timestamp(timestamp: str) -> Optional[datetime]:
    """
    Converts the timestamp format returned by the API
    
    Parameters
    ----------
    timestamp : str
        The string containing the timestamp.
    
    Returns
    -------
    Optional[datetime]
        A converted datetime object.
        None is returned if an empty string was passed.
    """
    if timestamp:
        return datetime.strptime(timestamp, "%m/%d/%Y %I:%M:%S %p")

def get(iterable: Iterable, **attrs):
    """
    Returns the first object from the `iterable` which attributes match the keyword arguments passed.

    You can use `__` to search in nested attributes.
    
    Parameters
    ----------
    iterable : Iterable
        The iterable to search in.
    **attrs
        The attributes to search for.
    
    Returns
    -------
    Any
        The first object from the iterable with attributes matching the keyword arguments passed.
        None is returned if the desired object couldn't be found in the iterable.
    """
    if len(attrs) == 1: # speed up checks for only one test atribute
        attr, val = attrs.popitem()
        getter = attrgetter(attr.replace('__', '.'))
        for element in iterable:
            if getter(element) == val:
                return element
        return None
    getters = [(attrgetter(attr.replace('__', '.')), val) for attr, val in attrs.items()]
    for element in iterable:
        for getter, val in getters:
            if getter(element) != val:
                break
        else:
            return element
    return None

def get_name_or_id(iterable: Iterable, name_or_id: Union[str, int], *, fuzzy: bool = False):
    """
    A helper function that searches for an object in an iterable based on it's
    `name` or `id` attributes. The attribute to search with is determined by the
    type of the input (int or str).
    
    Parameters
    ----------
    iterable : Iterable
        The iterable to search in.
    name_or_id : Union[str, int]
        The Name or ID of the object you're searching for.
    fuzzy : bool
        When set to True, makes the Name search case insensitive.
        Defaults to False.
    
    Returns
    -------
    Any
        The first object with matching Name or ID passed.
        None is returned if such object couldn't be found. 
    """
    if isinstance(name_or_id, int):
        return get(iterable, id=name_or_id)
    elif isinstance(name_or_id, str):
        if fuzzy:
            # we have to do it manually here
            matches = [i for i in iterable if i.name.lower() == name_or_id.lower()]
            return matches[0] if matches else None
        else:
            return get(iterable, name=name_or_id)

async def expand_partial(iterable: Iterable) -> AsyncGenerator:
    """
    A helper async generator that can be used to automatically expand PartialPlayer and PartialMatch objects for you.
    Any other object found in the `iterable` is passed unchanged.

    The following classes are converted:
        PartialPlayer -> Player
        PartialMatch -> Match
    
    Parameters
    ----------
    iterable : Iterable
        The iterable containing partial objects.
    
    Returns
    -------
    AsyncGenerator
        An async generator yielding expanded versions of each partial object.
    """
    from .player import PartialPlayer # cyclic imports
    from .match import PartialMatch # cyclic imports
    for i in iterable:
        if isinstance(i, (PartialPlayer, PartialMatch)):
            p = await i.expand()
            yield p
        else:
            yield i

class Duration(timedelta):
    """
    Represents a duration. Allows for easy conversion between time units.
    """
    def total_days(self) -> float:
        """
        The total amount of days within the duration as a float.
        """
        return super().total_seconds() / 86400

    def total_hours(self) -> float:
        """
        The total amount of hours within the duration as a float.
        """
        return super().total_seconds() / 3600
    
    def total_minutes(self) -> float:
        """
        The total amount of minutes within the duration as a float.
        """
        return super().total_seconds() / 60
    
    def total_seconds(self) -> float:
        """
        The total amount of seconds within the duration as a float.
        """
        return super().total_seconds()

class Status:
    """
    Represets a single server status.

    Attributes
    ----------
    platform : str
        A string denoting which platform this status is for.
    environment : str
        A string denoting which environment this server is running in.
        This is usually `live` or `pts`.
    up : bool
        True if the server is UP, False otherwise.
    limited_access : bool
        True if this servers has limited access, False otherwise.
    version : str
        The current version of this server.
    """
    def __init__(self, status_data: dict):
        self.platform = status_data["platform"]
        self.environment = status_data["environment"]
        self.up = status_data["status"] == "UP"
        self.limited_access = status_data["limited_access"]
        self.version = status_data["version"]

class ServerStatus:
    """
    An object representing the current HiRez server's status.

    Attributes
    ----------
    all_up : bool
        True if all live servers are UP, False otherwise.
        Note that this doesn't include PTS.
    limited_access : bool
        True if at least one live server has limited access, False otherwise.
        Note that this doesn't include PTS.
    all_statuses : List[Status]
        A list of all available statuses.
    
    Attributes below are added dynamically, for the sake of easy access only.
    Please note that they should (but may not) be available at all times.

    pc : Status
        Status for the PC platform.
    ps4 : Status
        Status for the PS4 platform.
    xbox : Status
        Status for the XBOX platform.
    switch : Status
        Status for the Nintendo Switch platform.
    pts : Status
        Status for the PTS server.
    """
    def __init__(self, status_data: list):
        self.all_up = True
        self.limited_access = False
        self.all_statuses = []
        for s in status_data:
            status = Status(s)
            self.all_statuses.append(status)
            if s["environment"] != "live":
                setattr(self, s["environment"], status)
            else:
                if not status.up:
                    self.all_up = False
                if status.limited_access:
                    self.limited_access = True
                setattr(self, s["platform"], status)

class PlayerStatus:
    """
    Represents the Player status.
    
    Attributes
    ----------
    player : Union[PartialPlayer, Player]
        The player this status is for.
    match_id : Optional[int]
        ID of the live match the player is currently in.
        None if the player isn't in a match.
    queue : Optional[Queue]
        The queue the player is currently playing in.
        None if the player isn't in a match.
    status : Activity
        An enumeration representing the current player status.
    """
    def __init__(self, player, status_data: dict):
        self.player = player
        self.match_id = status_data["Match"] or None
        self.queue = Queue.get(status_data["match_queue_id"])
        self.status = Activity.get(status_data["status"])
    
    # TODO: implement this
    # async def get_live_match(self) -> Match:
    #     from .match import Match # cyclic imports
    #     if self.match_id:
    #         response = await self.request("getmatchdetails", [self.match_id])
    #         return Match(self, language, response)
