from __future__ import annotations

from math import nan
from functools import wraps
from datetime import datetime
from abc import abstractmethod
from typing import (
    Optional, Union, List, Tuple, Generator, Awaitable, TypeVar, Literal, cast, TYPE_CHECKING
)

from . import responses
from .enums import Queue, Region

if TYPE_CHECKING:
    from .items import Device
    from .cache import DataCache, CacheEntry
    from .champion import Champion, Skin
    from .player import PartialPlayer, Player


__all__ = [
    "CacheClient",
    "CacheObject",
    "Expandable",
    "WinLoseMixin",
    "KDAMixin",
    "MatchMixin",
    "MatchPlayerMixin",
]
_A = TypeVar("_A")


class CacheClient:
    """
    Abstract base class that has to be met by most (if not all) objects that interact with the API.

    Provides access to the core of this wrapper, that is the `.request` method
    and the cache system.
    """
    def __init__(self, api: DataCache):
        self._api = api


class CacheObject:
    """
    Base class representing objects that can be returned from the data cache.
    You will sometimes find these on objects returned from the API, when the cache was either
    incomplete or disabled.

    Attributes
    ----------
    id : int
        The object's ID.\n
        Defaults to ``0`` if not set.
    name : str
        The object's name.\n
        Defaults to ``Unknown`` if not set.
    """
    def __init__(self, *, id: int = 0, name: str = "Unknown"):
        self._id: int = id
        self._name: str = name
        self._hash: Optional[int] = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self._name}({self._id})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            if self._id != 0 and other._id != 0:
                return self._id == other._id
            elif self._name != "Unknown" and other._name != "Unknown":
                return self._name == other._name
        return NotImplemented

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.__class__.__name__, self._name, self._id))
        return self._hash


class Expandable(Awaitable[_A]):
    """
    An abstract class that can be used to make partial objects "expandable" to their full version.

    Subclasses should overwrite the `_expand` method with proper implementation, returning
    the full expanded object.
    """
    # Subclasses will have their `_expand` method doc linked as the `__await__` doc.
    def __init_subclass__(cls):
        # Create a new await method
        # Copy over the docstring and annotations
        @wraps(cls._expand)
        def __await__(self: Expandable[_A]):
            return self._expand().__await__()
        # Attach the method to the subclass
        setattr(cls, "__await__", __await__)

    # solely to satisfy MyPy
    def __await__(self) -> Generator[_A, None, _A]:
        raise NotImplementedError

    @abstractmethod
    async def _expand(self) -> _A:
        raise NotImplementedError


class WinLoseMixin:
    """
    Represents player's wins and losses. Contains useful helper attributes.

    Attributes
    ----------
    wins : int
        The amount of wins.
    losses : int
        The amount of losses.
    """
    def __init__(self, *, wins: int, losses: int):
        self.wins = wins
        self.losses = losses

    @property
    def matches_played(self) -> int:
        """
        The amount of matches played. This is just ``wins + losses``.

        :type: int
        """
        return self.wins + self.losses

    @property
    def winrate(self) -> float:
        """
        The calculated winrate as a fraction.\n
        `nan` is returned if there was no matches played.

        :type: float
        """
        return self.wins / self.matches_played if self.matches_played > 0 else nan

    @property
    def winrate_text(self) -> str:
        """
        The calculated winrate as a percentage string of up to 3 decimal places accuracy.\n
        The format is: ``"48.213%"``\n
        ``"N/A"`` is returned if there was no matches played.

        :type: str
        """
        return f"{round(self.winrate * 100, 3)}%" if self.matches_played > 0 else "N/A"


class KDAMixin:
    """
    Represents player's kills, deaths and assists. Contains useful helper attributes.

    Attributes
    ----------
    kills : int
        The amount of kills.
    deaths : int
        The amount of deaths.
    assists : int
        The amount of assists.
    """
    def __init__(self, *, kills: int, deaths: int, assists: int):
        self.kills: int = kills
        self.deaths: int = deaths
        self.assists: int = assists

    @property
    def kda(self) -> float:
        """
        The calculated KDA.\n
        The formula is: ``(kills + assists / 2) / deaths``.\n
        `nan` is returned if there was no deaths.

        :type: float
        """
        return (self.kills + self.assists / 2) / self.deaths if self.deaths > 0 else nan

    @property
    def kda2(self) -> float:
        """
        The calculated KDA.\n
        The formula is: ``(kills + assists / 2) / max(deaths, 1)``, treating 0 and 1 deaths
        the same, meaning this will never return `nan`.

        :type: float
        """
        return (self.kills + self.assists / 2) / max(self.deaths, 1)

    @property
    def df(self) -> int:
        """
        The Dominance Factor.\n
        The formula is: ``kills * 2 + deaths * -3 + assists``.\n
        The value signifies how "useful" the person was to the team overall.
        Best used when scaled and compared between team members in a match (allied and enemy).

        :type: int
        """
        return self.kills * 2 + self.deaths * -3 + self.assists

    @property
    def kda_text(self) -> str:
        """
        Kills, deaths and assists as a slash-delimited string.\n
        The format is: ``kills/deaths/assists``, or ``1/2/3``.

        :type: str
        """
        return f"{self.kills}/{self.deaths}/{self.assists}"


class MatchMixin:
    """
    Represents basic information about a match.

    Attributes
    ----------
    id : int
        The match ID.
    queue : Queue
        The queue this match was played in.
    region : Region
        The region this match was played in.
    timestamp : datetime.datetime
        A timestamp of when this match happened.
    duration : Duration
        The duration of the match.
    map_name : str
        The name of the map played.
    score : Tuple[int, int]
        The match's ending score.
    winning_team : Literal[1, 2]
        The winning team of this match.
    """
    def __init__(
        self, match_data: Union[responses.MatchPlayerObject, responses.HistoryMatchObject]
    ):
        self.id: int = match_data["Match"]
        if "hasReplay" in match_data:
            # we're in a full match data
            match_data = cast(responses.MatchPlayerObject, match_data)
            stamp = match_data["Entry_Datetime"]
            queue = match_data["match_queue_id"]
            score = (match_data["Team1Score"], match_data["Team2Score"])
        else:
            # we're in a partial (player history) match data
            match_data = cast(responses.HistoryMatchObject, match_data)
            stamp = match_data["Match_Time"]
            queue = match_data["Match_Queue_Id"]
            my_team = match_data["TaskForce"]
            other_team = 1 if my_team == 2 else 2
            score = (
                match_data[f"Team{my_team}Score"],  # type: ignore[misc]
                match_data[f"Team{other_team}Score"],  # type: ignore[misc]
            )
        self.queue = Queue(queue, _return_default=True)
        self.region = Region(match_data["Region"], _return_default=True)
        from .utils import _convert_timestamp, _convert_map_name, Duration  # circular imports
        self.timestamp: datetime = _convert_timestamp(stamp)
        self.duration = Duration(seconds=match_data["Time_In_Match_Seconds"])
        self.map_name: str = _convert_map_name(match_data["Map_Game"])
        if self.queue.is_tdm():
            # Score correction for TDM matches
            score = (score[0] + 36, score[1] + 36)
        self.score: Tuple[int, int] = score
        self.winning_team: Literal[1, 2] = match_data["Winning_TaskForce"]


class MatchPlayerMixin(KDAMixin, CacheClient):
    """
    Represents basic information about a player in a match.

    Attributes
    ----------
    player : Union[PartialPlayer, Player]
        The player who participated in this match.\n
        This is usually a new partial player object.\n
        All attributes, Name, ID and Platform, should be present.
    champion : Union[Champion, CacheObject]
        The champion used by the player in this match.\n
        With incomplete cache, this will be a `CacheObject` with the name and ID set.
    loadout : MatchLoadout
        The loadout used by the player in this match.
    items : List[MatchItem]
        A list of items bought by the player during this match.
    credits : int
        The amount of credits earned this match.
    kills : int
        The amount of player kills.
    deaths : int
        The amount of deaths.
    assists : int
        The amount of assists.
    damage_done : int
        The amount of damage dealt.
    damage_bot : int
        The amount of damage done by the player's bot after they disconnected.
    damage_taken : int
        The amount of damage taken.
    damage_mitigated : int
        The amount of damage mitigated (shielding).
    healing_done : int
        The amount of healing done to other players.
    healing_bot : int
        The amount of healing done by the player's bot after they disconnected.
    healing_self : int
        The amount of healing done to self (self-sustain).
    objective_time : int
        The amount of objective time the player got, in seconds.
    multikill_max : int
        The maximum multikill player did during the match.
    skin : Union[Skin, CacheObject]
        The skin the player had equipped for this match.\n
        With incomplete cache, this will be a `CacheObject` with the name and ID set.
    team_number : Literal[1, 2]
        The team this player belongs to.
    team_score : int
        The score of the player's team.
    winner : bool
        `True` if the player won this match, `False` otherwise.
    """
    def __init__(
        self,
        player: Union[Player, PartialPlayer],
        cache_entry: Optional[CacheEntry],
        match_data: Union[responses.MatchPlayerObject, responses.HistoryMatchObject],
    ):
        CacheClient.__init__(self, player._api)
        if "hasReplay" in match_data:
            # we're in a full match data
            match_data = cast(responses.MatchPlayerObject, match_data)
            creds = match_data["Gold_Earned"]
            kills = match_data["Kills_Player"]
            damage = match_data["Damage_Done_Physical"]
            champion_name = match_data["Reference_Name"]
        else:
            # we're in a partial (player history) match data
            match_data = cast(responses.HistoryMatchObject, match_data)
            creds = match_data["Gold"]
            kills = match_data["Kills"]
            damage = match_data["Damage"]
            champion_name = match_data["Champion"]
        KDAMixin.__init__(
            self, kills=kills, deaths=match_data["Deaths"], assists=match_data["Assists"]
        )
        # Champion
        champion_id = match_data["ChampionId"]
        champion: Optional[Union[Champion, CacheObject]] = None
        if cache_entry is not None:
            champion = cache_entry.champions.get(champion_id)
        if champion is None:
            champion = CacheObject(id=champion_id, name=champion_name)
        self.champion: Union[Champion, CacheObject] = champion
        # Skin
        skin_id = match_data["SkinId"]
        skin: Optional[Union[Skin, CacheObject]] = None
        if cache_entry is not None:
            skin = cache_entry.skins.get(skin_id)
        if skin is None:  # pragma: no cover
            skin = CacheObject(id=skin_id, name=match_data["Skin"])
        self.skin: Union[Skin, CacheObject] = skin
        # Other
        self.player: Union[Player, PartialPlayer] = player
        self.credits: int = creds
        self.damage_done: int = damage
        self.damage_bot: int = match_data["Damage_Bot"]
        self.damage_taken: int = match_data["Damage_Taken"]
        self.damage_mitigated: int = match_data["Damage_Mitigated"]
        self.healing_done: int = match_data["Healing"]
        self.healing_bot: int = match_data["Healing_Bot"]
        self.healing_self: int = match_data["Healing_Player_Self"]
        self.objective_time: int = match_data["Objective_Assists"]
        self.multikill_max: int = match_data["Multi_kill_Max"]
        self.team_number: Literal[1, 2] = match_data["TaskForce"]
        self.team_score: int = match_data[f"Team{self.team_number}Score"]  # type: ignore[misc]
        self.winner: bool = self.team_number == match_data["Winning_TaskForce"]

        from .items import MatchLoadout, MatchItem  # cyclic imports
        self.items: List[MatchItem] = []
        for i in range(1, 5):
            item_id = match_data[f"ActiveId{i}"]  # type: ignore[misc]
            if not item_id:
                continue
            item: Optional[Union[Device, CacheObject]] = None
            if cache_entry is not None:
                item = cache_entry.items.get(item_id)
            if item is None:
                if "hasReplay" in match_data:
                    # we're in a full match data
                    item_name = match_data[f"Item_Active_{i}"]  # type: ignore[misc]
                else:
                    # we're in a partial (player history) match data
                    item_name = match_data[f"Active_{i}"]  # type: ignore[misc]
                item = CacheObject(id=item_id, name=item_name)
            if "hasReplay" in match_data:
                # we're in a full match data
                level = match_data[f"ActiveLevel{i}"] + 1  # type: ignore[misc]
            else:
                # we're in a partial (player history) match data
                level = match_data[f"ActiveLevel{i}"] // 4 + 1  # type: ignore[misc]
            self.items.append(MatchItem(item, level))
        self.loadout = MatchLoadout(cache_entry, match_data)

    @property
    def shielding(self) -> int:
        """
        This is an alias for the `damage_mitigated` attribute.

        :type: int
        """
        return self.damage_mitigated
