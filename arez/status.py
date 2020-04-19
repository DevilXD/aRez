from datetime import datetime
from typing import Optional, Union, List, Dict, Literal, TYPE_CHECKING

from .match import LiveMatch
from .mixins import APIClient
from .enumerations import Activity, Queue, Language

if TYPE_CHECKING:
    from .player import PartialPlayer, Player  # noqa


class Status:
    """
    Represets a single server status.

    You can find these on the `ServerStatus` object.

    Attributes
    ----------
    platform : Literal["pc", "ps4", "xbox", "switch", "pts"]
        A string denoting which platform this status is for.
    up : bool
        `True` if the server is UP, `False` otherwise.
    limited_access : bool
        `True` if this server has limited access, `False` otherwise.
    version : str
        The current version of this server.\n
        This will be an empty string if the information wasn't available.
    """
    def __init__(self, status_data: dict):
        self.platform: Literal["pc", "ps4", "xbox", "switch", "pts"] = status_data["platform"]
        env = status_data["environment"]
        if env == "pts":
            self.platform = env
        self.up: bool = status_data["status"] == "UP"
        self.limited_access: bool = status_data["limited_access"]
        self.version: str = status_data["version"] or ''

    def __repr__(self) -> str:
        up = "Up" if self.up else "Down"
        la_text = ''
        if self.limited_access:
            la_text = ", Limited Access"
        return f"{self.__class__.__name__}({self.platform}: {up}{la_text})"


class ServerStatus:
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
    statuses : List[Status]
        A list of all available statuses.
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
        self.pc: Status
        self.ps4: Status
        self.xbox: Status
        self.switch: Status
        self.pts: Status
        self.statuses: List[Status] = []
        for s in status_data:
            status = Status(s)
            self.statuses.append(status)
            platform = status.platform
            setattr(self, platform, status)
            if platform != "pts":
                if not status.up:
                    self.all_up = False
                if status.limited_access:
                    self.limited_access = True

    def __repr__(self) -> str:
        status = "All Up" if self.all_up else "Partially Down"
        la_text = ''
        if self.limited_access:
            la_text = ", Limited Access"
        return f"{self.__class__.__name__}({status}{la_text})"


class PlayerStatus(APIClient):
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
        An enumeration representing the current player status.
    """
    def __init__(self, player: Union["PartialPlayer", "Player"], status_data: dict):
        super().__init__(player._api)
        self.player = player
        self.live_match_id: Optional[int] = status_data["Match"] or None
        self.queue: Queue = Queue(status_data["match_queue_id"], return_default=True)
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
        response = await self.player._api.request("getmatchplayerdetails", self.live_match_id)
        if not response:
            return None
        if response[0]["ret_msg"]:
            # unsupported queue
            return None
        players: Dict[int, Player] = {}
        if expand_players:
            players_list = await self._api.get_players((int(p["playerId"]) for p in response))
            players = {p.id: p for p in players_list}
        return LiveMatch(self._api, language, response, players)
