from enum import Enum
from datetime import datetime
from typing import Union, Optional, Iterable, AsyncGenerator

from .enumerations import Activity, Queue

def convert_timestamp(timestamp: str) -> Optional[datetime]:
    if timestamp:
        return datetime.strptime(timestamp, "%m/%d/%Y %I:%M:%S %p")

def get(iterable, **attrs):
    for element in iterable:
        for attr, val in attrs.items():
            if getattr(element, attr) != val:
                break
        else:
            return element
    return None

def get_name_or_id(iterable: Iterable, name_or_id: Union[str, int]):
    if isinstance(name_or_id, int):
        return get(iterable, id = name_or_id)
    elif isinstance(name_or_id, str):
        return get(iterable, name = name_or_id)

async def expand_partial(iterable: Iterable) -> AsyncGenerator:
    from .player import PartialPlayer # cyclic imports
    from .match import PartialMatch # cyclic imports
    for i in iterable:
        if isinstance(i, (PartialPlayer, PartialMatch)):
            p = await i.expand()
            yield p
        else:
            yield i

class ServerStatus:
    def __init__(self, status_data: list):
        self.all_up = True
        self.limited_access = False
        for s in status_data:
            status = {"limited_access": s["limited_access"], "up": s["status"] == "UP", "version": s["version"]}
            if s["environment"] != "live":
                setattr(self, s["environment"], status)
            else:
                if not status["up"]:
                    self.all_up = False
                if status["limited_access"]:
                    self.limited_access = True
                setattr(self, s["platform"], status)

class PlayerStatus:
    def __init__(self, player, status_data: dict):
        self.player = player
        self.match_id = status_data["Match"] or None
        self.queue = Queue.get(status_data["match_queue_id"]) # pylint: disable=no-member
        self.status = Activity(status_data["status"])
    
    # TODO: implement this
    # async def get_live_match(self) -> Match:
    #     from .match import Match # cyclic imports
    #     if self.match_id:
    #         response = await self.request("getmatchdetails", [self.match_id])
    #         return Match(self, language, response)
