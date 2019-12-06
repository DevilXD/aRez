from typing import Optional
from datetime import datetime

from .match import LiveMatch
from .enumerations import Activity, Queue, Language


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
        `True` if the server is UP, `False` otherwise.
    limited_access : bool
        `True` if this servers has limited access, `False` otherwise.
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
    timestamp : datetime
        A UTC timestamp denoting when this status was fetched.
    all_up : bool
        `True` if all live servers are UP, `False` otherwise.
        Note that this doesn't include PTS.
    limited_access : bool
        `True` if at least one live server has limited access, `False` otherwise.
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
        self.timestamp = datetime.utcnow()
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

    def __repr__(self) -> str:
        status = "All UP" if self.all_up else "Not all UP"
        limited = "LIMITED" if self.limited_access else "NOT LIMITED"
        return "{0.__class__.__name__}({1} / {2})".format(self, status, limited)


class PlayerStatus:
    """
    Represents the Player status.

    Attributes
    ----------
    player : Union[PartialPlayer, Player]
        The player this status is for.
    live_match_id : Optional[int]
        ID of the live match the player is currently in.
        `None` if the player isn't in a match.
    queue : Optional[Queue]
        The queue the player is currently playing in.
        `None` if the player isn't in a match.
    status : Activity
        An enumeration representing the current player status.
    """
    def __init__(self, player, status_data: dict):
        self._api = player._api
        self.player = player
        self.live_match_id = status_data["Match"] or None
        self.queue = (
            status_data["match_queue_id"]
            and Queue.get(status_data["match_queue_id"])
            or None
        )
        self.status = Activity.get(status_data["status"])

    def __repr__(self) -> str:
        return "{0.player.name}({0.player.id}): {0.status.name}".format(self)

    async def get_live_match(self, language: Language = Language.English) -> Optional[LiveMatch]:
        """
        Fetches a live match the player is currently in.

        Uses up a single request.

        Parameters
        ----------
        language : Optional[Language]
            The language to fetch the match in, Language.English by default.

        Returns
        -------
        Optional[LiveMatch]
            The live match requested.
            `None` is returned if the player isn't in a live match,
            or the match is played in an unsupported queue (customs).
        """
        # ensure we have champion information first
        await self._api.get_champion_info(language)
        if self.live_match_id:
            response = await self.player._api.request("getmatchplayerdetails", self.live_match_id)
            if response and response[0] and response[0]["ret_msg"]:
                return None
            return LiveMatch(self._api, language, response)
