from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union, List, Dict, Tuple, Literal, cast, TYPE_CHECKING

from .statuspage import colors
from .mixins import CacheClient
from .enums import Activity, Queue
from .exceptions import ArezException
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


def _convert_status(
    up: Optional[bool], limited_access: Optional[bool], status: Optional[str], color: Optional[int]
) -> Tuple[bool, bool, str, int]:
    """
    A function responsible for the logic behind merging server status data, from the official API
    and StatusPage.
    Depending on the availability, the only accepted input parameters combinations are:

    • up, limited_access, None, None - only official API available
    • None, None, status, color - only StatusPage available
    • up, limited_access, status, color - both available

    Any other combination is a library error, and should raise an `arez.ArezException`.

    Parameters
    ----------
    up : Optional[bool]
        Server status flag from the official API.\n
        `None` when not available.
    limited_access : Optional[bool]
        Limited access flag from the official API.\n
        `None` when not available.
    status : Optional[str]
        StatusPage group status description.\n
        `None` when not available.
    color : Optional[int]
        StatusPage group color.\n
        `None` when not available.

    Returns
    -------
    Tuple[bool, bool, str, int]
        A tuple representing merged status: ``(up, limited_access, status, color)``.
    """
    first_set = sum((up is not None, limited_access is not None))
    second_set = sum((status is not None, color is not None))
    if first_set % 2 != 0 or second_set % 2 != 0:  # pragma: no cover
        # checks if any of the two sets has only one argument present, instead of both
        raise ArezException("Either of the two status input groups had only one argument passed")
    elif first_set == 0 and second_set == 0:  # pragma: no cover
        # checks if either of the two sets was passed at all
        raise ArezException("No status input groups were passed")

    if up is None and limited_access is None and status is not None and color is not None:
        # StatusPage only
        if status in ("Operational", "Degraded Performance"):  # pragma: no branch
            final_up = True
        else:
            final_up = False
        return (final_up, False, status, color)
    # official API definitely exists here
    assert up is not None and limited_access is not None
    status_color: Tuple[str, int] = ("Operational", colors["green"])
    if not up:
        status_color = ("Outage", colors["red"])
    elif limited_access:
        status_color = ("Limited Access", colors["yellow"])
    if status is not None and color is not None:
        # StatusPage is also present
        if (
            (not up or limited_access)
            and status not in ("Operational", "Degraded Performance")
            or up and not limited_access and status == "Degraded Performance"
        ):
            status_color = (status, color)
    return (up, limited_access, *status_color)


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
        self.up: bool
        self.limited_access: bool
        self.status: str
        self.color: int

        platform: str = status_data["platform"]
        env = status_data["environment"]
        if env == "pts":
            platform = env
        self.platform: _platforms = _convert_platform(platform)
        self.version: str = status_data["version"] or ''

        status_color: Tuple[Optional[str], Optional[int]] = (None, None)
        self.incidents: List[Incident] = []
        self.maintenances: List[Maintenance] = []
        # this also removes the component from the dictionary
        if comp := components.pop(self.platform.lower(), None):
            status_color = (comp.status, comp.color)
            self.incidents = comp.incidents
            self.maintenances = comp.maintenances
        self.up, self.limited_access, self.status, self.color = _convert_status(
            status_data["up"], status_data["limited_access"], *status_color
        )

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
        self.up, self.limited_access, self.status, self.color = _convert_status(
            None, None, component.status, component.color
        )
        self.version = ''  # no info on this here
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
        self.all_up: bool
        self.limited_access: bool
        self.status: str
        self.color: int

        self.statuses: Dict[str, Status] = {}
        # each StatusPage component for Paladins starts with "Paladins ...", we need to strip that
        components: Dict[str, Component] = {}
        if group is not None:
            group_name: str = group.name
            for comp in group.components:
                comp_name = comp.name
                if comp_name.startswith(group_name):  # pragma: no branch
                    comp_name = comp_name[len(group_name):].strip()
                components[comp_name.lower()] = comp
        statuses: List[Status] = []
        # match keys with existing official data, and add StatusPage data
        # note: this may not run at all, if the official API's response was empty
        for status_data in api_status:
            statuses.append(Status(status_data, components))
        # add any remaining StatusPage components data (can be none left)
        for platform_name, comp in components.items():
            statuses.append(Status.from_component(platform_name, comp))
        # handle the rest
        all_up = True
        limited_access = False
        for status in statuses:
            platform = status.platform.lower()
            self.statuses[platform] = status
            if platform == "pts":  # PTS status doesn't change the overall status
                continue
            if not status.up:
                all_up = False
            if status.limited_access:
                limited_access = True
        status_color: Tuple[Optional[str], Optional[int]] = (None, None)
        self.incidents: List[Incident] = []
        self.maintenances: List[Maintenance] = []
        if group is not None:
            status_color = (group.status, group.color)
            self.incidents = group.incidents
            self.maintenances = group.maintenances
        self.all_up, self.limited_access, self.status, self.color = _convert_status(
            all_up, limited_access, *status_color
        )

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
