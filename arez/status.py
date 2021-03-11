from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union, List, Dict, Literal, cast, TYPE_CHECKING

from .statuspage import colors
from .mixins import CacheClient
from .enums import Activity, Queue
from .match import LiveMatch, _get_players

if TYPE_CHECKING:
    from .enums import Language
    from .player import PartialPlayer, Player
    from .statuspage import Component, ComponentGroup, Incident, Maintenance


__all__ = [
    "Status",
    "ServerStatus",
    "PlayerStatus",
]


_platforms = Literal["PC", "PS4", "Xbox", "Switch", "Epic", "PTS"]


def _convert_platform(platform: str) -> _platforms:
    if platform.startswith('p'):
        text = platform.upper()
    else:
        text = platform.capitalize()
    return cast(_platforms, text)


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
    def __init__(self, status_data: Dict[str, Any], components: Dict[str, Component]):
        platform: str = status_data["platform"]
        env = status_data["environment"]
        if env == "pts":
            platform = env
        self.platform: _platforms = _convert_platform(platform)
        self.up: Optional[bool] = status_data["up"]
        self.limited_access: bool = status_data["limited_access"]
        self.version: str = status_data["version"] or ''
        self.status: str = "Operational"
        self.color: int = colors["green"]
        if not self.up:
            self.status = "Outage"
            self.color = colors["red"]
        elif self.limited_access:
            self.status = "Limited access"
            self.color = colors["yellow"]
        self.incidents: List[Incident] = []
        self.maintenances: List[Maintenance] = []
        # this also removes the component from the dictionary
        if comp := components.pop(self.platform.lower(), None):
            status = comp.status
            if (
                (not self.up or self.limited_access) and status != "Operational"
                or self.up and not self.limited_access and status == "Degraded Performance"
            ):  # pragma: no cover
                if "Outage" in status:
                    self.up = False
                self.status = status
                self.color = comp.color
            self.incidents = comp.incidents
            self.maintenances = comp.maintenances

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.platform}: {self.status})"

    def __eq__(self, other: object) -> bool:  # pragma: no cover
        if not isinstance(other, self.__class__):
            return NotImplemented
        return all(
            getattr(self, attr_name) == getattr(other, attr_name)
            for attr_name in ("up", "limited_access", "version", "status")
        )

    @classmethod
    def from_component(cls, platform_name: str, component: Component):
        # build it from scratch
        self: Status = super().__new__(cls)
        self.platform = _convert_platform(platform_name)
        self.limited_access = False  # no info on this here
        self.version = ''  # same here
        status: str = component.status
        if status in ("Operational", "Degraded Performance"):  # pragma: no branch
            self.up = True
        else:
            self.up = False  # pragma: no cover
        self.status = status
        self.color = component.color
        self.incidents = component.incidents
        self.maintenances = component.maintenances
        return self

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
        ``pc``, ``ps4``, ``xbox``, ``switch``, ``epic`` and ``pts``.
    incidents : List[Incident]
        A list of incidents affecting the current server status.
    maintenances : List[Maintenance]
        A list of maintenances that will (or are) affect the server status in the future.
    """
    def __init__(self, api_status: List[Dict[str, Any]], group: Optional[ComponentGroup]):
        self.timestamp = datetime.utcnow()
        self.all_up = True
        self.limited_access = False
        self.status: str = "Operational"
        self.color: int = colors["green"]
        self.statuses: Dict[str, Status] = {}
        self.incidents: List[Incident] = []
        self.maintenances: List[Maintenance] = []
        # each StatusPage component for Paladins starts with "Paladins ...", we need to strip that
        components: Dict[str, Component] = {}
        if group is not None:
            group_name: str = group.name
            for comp in group.components:
                comp_name = comp.name
                if comp_name.startswith(group_name):  # pragma: no branch
                    comp_name = comp_name[len(group_name):].strip()
                components[comp_name.lower()] = comp
        # match keys with existing official data, and add StatusPage data
        # note: this may not run at all, if the official API's response was empty
        for status_data in api_status:
            self._add_status(Status(status_data, components))
        # add any remaining StatusPage components data (can be none left)
        for platform_name, comp in components.items():
            self._add_status(Status.from_component(platform_name, comp))
        # handle the rest
        if not self.all_up:
            self.status = "Outage"
            self.color = colors["red"]
        elif self.limited_access:
            self.status = "Limited access"
            self.color = colors["yellow"]
        if group is not None:
            status = group.status
            if (
                (not self.all_up or self.limited_access) and status != "Operational"
                or self.all_up and not self.limited_access and status == "Degraded Performance"
            ):  # pragma: no cover
                if "Outage" in status:
                    self.all_up = False
                self.status = status
                self.color = group.color
            self.incidents = group.incidents
            self.maintenances = group.maintenances

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.status})"

    def __eq__(self, other: object) -> bool:  # pragma: no cover
        if not isinstance(other, self.__class__):
            return NotImplemented
        # check attributes
        if not all(
            getattr(self, attr_name) == getattr(other, attr_name)
            for attr_name in ("all_up", "limited_access", "status")
        ):
            return False
        # incidents
        if (
            len(self.incidents) != len(other.incidents)
            or (
                self.incidents and other.incidents
                and self.incidents[0].updated_at != other.incidents[0].updated_at
            )
        ):
            return False
        # maintenances
        if (
            len(self.incidents) != len(other.incidents)
            or (
                self.maintenances and other.maintenances
                and self.maintenances[0].updated_at != other.maintenances[0].updated_at
            )
        ):
            return False
        # compare all stored statuses
        return self.statuses == other.statuses

    def _add_status(self, status: Status):
        platform = status.platform.lower()
        if platform != "pts":
            if not status.up:
                self.all_up = False
            if status.limited_access:
                self.limited_access = True
        self.statuses[platform] = status

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
        cache_entry = self._api.get_entry(language)
        response = await self._api.request("getmatchplayerdetails", self.live_match_id)
        if not response:
            return None
        if response[0]["ret_msg"]:
            # unsupported queue
            return None
        players_dict: Dict[int, Player] = {}
        if expand_players:
            players_dict = await _get_players(self._api, (int(p["playerId"]) for p in response))
        return LiveMatch(self._api, cache_entry, response, players_dict)
