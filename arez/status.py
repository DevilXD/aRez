from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union, List, Dict, Literal, cast, TYPE_CHECKING

from .statuspage import colors
from .mixins import CacheClient
from .match import LiveMatch, _get_players
from .enums import Activity, Queue, Language

if TYPE_CHECKING:
    from .player import PartialPlayer, Player  # noqa
    from .statuspage import ComponentGroup, Component, Incident, ScheduledMaintenance


__all__ = [
    "Status",
    "ServerStatus",
    "PlayerStatus",
]


def _convert_platform(platform: str) -> str:
    if platform.startswith('p'):
        return platform.upper()
    return platform.capitalize()


class Status:
    """
    Represets a single server status.

    You can find these on the `ServerStatus` object.

    Attributes
    ----------
    platform : Literal["PC", "PS4", "Xbox", "Switch", "PTS"]
        A string denoting which platform this status is for.
    up : bool
        `True` if the server is UP, `False` otherwise.
    limited_access : bool
        `True` if this server has limited access, `False` otherwise.
    version : str
        The current version of this server.\n
        This will be an empty string if the information wasn't available.
    status : Literal["Operational",\
        "Under Maintenance",\
        "Degraded Performance",\
        "Partial Outage",\
        "Major Outage"]
        This server's status description.
    color : int
        The color assiciated with this server's status.
    incidents : List[Incident]
        A list of incidents affecting this server status.
    scheduled_maintenances : List[ScheduledMaintenance]
        A list of scheduled maintenances that will (or are)
        affect this server status in the future.
    """
    def __init__(self, status_data: Dict[str, Any]):
        platform: str = status_data["platform"]
        env = status_data["environment"]
        if env == "pts":
            platform = env
        self.platform: Literal["PC", "PS4", "Xbox", "Switch", "PTS"] = cast(
            Literal["PC", "PS4", "Xbox", "Switch", "PTS"], _convert_platform(platform)
        )
        self.up: bool = status_data["status"] == "UP"
        self.limited_access: bool = status_data["limited_access"]
        self.version: str = status_data["version"] or ''
        self.status: str = "Operational"
        self.color: int = colors["green"]
        if not self.up:
            self.status = "Down"
            self.color = colors["red"]
        elif self.limited_access:
            self.status = "Limited access"
            self.color = colors["yellow"]
        self.incidents: List[Incident] = []
        self.scheduled_maintenances: List[ScheduledMaintenance] = []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.platform}: {self.status})"

    def _attach_component(self, component: Component):
        if component.status != "Operational":  # pragma: no cover
            self.status = component.status
            self.color = component.color
        self.incidents = component.incidents
        self.scheduled_maintenances = component.scheduled_maintenances

    @property
    def colour(self):
        return self.color  # pragma: no cover


class ServerStatus(CacheClient):
    """
    An object representing the current HiRez server's status.

    You can get this from the `PaladinsAPI.get_server_status` method.

    Attributes
    ----------
    timestamp : datetime.datetime
        A UTC timestamp denoting when this status was fetched.
    all_up : bool
        `True` if all live servers are UP, `False` otherwise.\n
        Note that this doesn't include PTS.
    limited_access : bool
        `True` if at least one live server has limited access, `False` otherwise.\n
        Note that this doesn't include PTS.
    status : Literal["Operational",\
        "Under Maintenance",\
        "Degraded Performance",\
        "Partial Outage",\
        "Major Outage"]
        The overall server status description.\n
        This represents the worst status of all individual server statuses.\n
        ``Under Maintenance`` is considered second worst.
    color : int
        The color associated with the current overall server status.\n
        There is an alias for this under ``colour``.
    statuses : Dict[str, Status]
        A dictionary of all individual available server statuses.\n
        The usual keys you should be able to find here are:
        ``pc``, ``ps4``, ``xbox``, ``switch`` and ``pts``.
    incidents : List[Incident]
        A list of incidents affecting the current server status.
    scheduled_maintenances : List[ScheduledMaintenance]
        A list of scheduled maintenances that will (or are) affect the server status in the future.
    """
    def __init__(self, status_data: List[Dict[str, Any]], group: ComponentGroup):
        self.timestamp = datetime.utcnow()
        self.all_up = True
        self.limited_access = False
        self.statuses: Dict[str, Status] = {}
        for s in status_data:
            status = Status(s)
            platform = status.platform.lower()
            self.statuses[platform] = status
            if platform != "pts":
                if not status.up:
                    self.all_up = False
                if status.limited_access:
                    self.limited_access = True
        # each StatusPage component for Paladins starts with "Paladins ...", we need to strip that
        group_name = group.name
        components: Dict[str, Component] = {}
        for comp in group.components:
            comp_name = comp.name
            if comp_name.startswith(group_name):  # pragma: no branch
                comp_name = comp_name[len(group_name):].strip()
            components[comp_name.lower()] = comp
        for status_name, status in self.statuses.items():
            if component := components.get(status_name):
                status._attach_component(component)
        self.status: str = group.status
        self.color: int = group.color
        if self.status == "Operational":  # pragma: no cover
            if not self.all_up:
                self.status = "Outage"
                self.color = colors["red"]
            elif self.limited_access:
                self.status = "Limited access"
                self.color = colors["yellow"]
        self.incidents: List[Incident] = group.incidents
        self.scheduled_maintenances: List[ScheduledMaintenance] = group.scheduled_maintenances

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.status})"

    @property
    def colour(self) -> int:
        return self.color  # pragma: no cover


class PlayerStatus(CacheClient):
    """
    Represents a Player's in-game status.

    You can get this from the `PartialPlayer.get_status` method.

    Attributes
    ----------
    player : Union[PartialPlayer, Player]
        The player this status is for.
    live_match_id : Optional[int]
        ID of the live match the player is currently in.\n
        `None` if the player isn't in a match.
    queue : Optional[Queue]
        The queue the player is currently playing in.\n
        `None` if the player isn't in a match.
    status : Activity
        An enum representing the current player status.
    """
    def __init__(self, player: Union[PartialPlayer, Player], status_data: Dict[str, Any]):
        super().__init__(player._api)
        self.player = player
        self.live_match_id: Optional[int] = status_data["Match"] or None
        queue: Optional[Queue] = None
        if queue_id := status_data["match_queue_id"]:
            queue = Queue(queue_id)
        self.queue: Optional[Queue] = queue
        self.status = Activity(status_data["status"])

    def __repr__(self) -> str:
        return f"{self.player.name}({self.player.id}): {self.status.name}"

    async def get_live_match(
        self, language: Optional[Language] = None, *, expand_players: bool = False
    ) -> Optional[LiveMatch]:
        """
        Fetches a live match the player is currently in.

        Uses up a single request.

        Parameters
        ----------
        language : Language
            The language to fetch the match in.\n
            Default language is used if not provided.
        expand_players : bool
            When set to `True`, partial player objects in the returned match object will
            automatically be expanded into full `Player` objects, if possible.\n
            Uses an addtional request to do the expansion.\n
            Defaults to `False`.

        Returns
        -------
        Optional[LiveMatch]
            The live match requested.\n
            `None` is returned if the player isn't in a live match,
            or the match is played in an unsupported queue (customs).
        """
        if not self.live_match_id:
            # nothing to fetch
            return None
        if language is None:
            language = self._api._default_language
        # ensure we have champion information first
        await self._api._ensure_entry(language)
        response = await self._api.request("getmatchplayerdetails", self.live_match_id)
        if not response:
            return None
        if response[0]["ret_msg"]:
            # unsupported queue
            return None
        players_dict: Dict[int, Player] = {}
        if expand_players:
            players_dict = await _get_players(self._api, (int(p["playerId"]) for p in response))
        return LiveMatch(self._api, language, response, players_dict)
