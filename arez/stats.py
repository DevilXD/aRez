from __future__ import annotations

from datetime import datetime
from typing import Optional, Union, Literal, cast, TYPE_CHECKING

from . import responses
from .enums import Rank
from .utils import Duration, _convert_timestamp
from .mixins import CacheObject, WinLoseMixin, KDAMixin

if TYPE_CHECKING:
    from .enums import Queue
    from .cache import CacheEntry
    from .champion import Champion
    from .player import PartialPlayer, Player


__all__ = [
    "DataUsed",
    "Stats",
    "RankedStats",
    "ChampionStats",
]


class DataUsed:
    """
    Represents API usage statistics.

    You can get this from the `PaladinsAPI.get_data_used` method.

    .. note::

        API sessions are automatically managed by the wrapper.
        The data provided here is meant solely for the API usage tracking purposes.

    .. note::

        The statistics are calculated over a rolling 24 hours window, meaning that each time
        you use one request, you will be getting it back exactly 24 hours later.
        Thus, there is no particular time at which these stats reset.

    Attributes
    ----------
    timestamp : datetime.datetime
        A timestamp of when these statistics were fetched.
    active_sessions_used : int
        The amount of active sessions currently being used.
    active_sessions_limit : int
        The maximum amount of active sessions you're allowed to have at the same time.\n
        The default value is ``50``.
    sessions_used : int
        The amount of sessions used within the last 24 hours.
    sessions_limit : int
        The maximum amount of sessions you're allowed to use within 24 hours.\n
        The default value is ``500``.
    sessions_lifetime : int
        The amount of time, in minutes, that needs to pass since your last request,
        for the session to be closed.\n
        Your next request is going to automatically start another session.
    requests_used : int
        The amount of requests used within the last 24 hours.
    requests_limit : int
        The maximum amount of requests you're allowed to use within 24 hours.\n
        The default value is ``7500``.
    """
    def __init__(self, data: responses.DataUsedObject):
        self.timestamp = datetime.utcnow()
        self.active_sessions_used: int = data["Active_Sessions"]
        self.active_sessions_limit: int = data["Concurrent_Sessions"]
        self.sessions_used: int = data["Total_Sessions_Today"]
        self.sessions_limit: int = data["Session_Cap"]
        self.sessions_lifetime: int = data["Session_Time_Limit"]
        self.requests_used: int = data["Total_Requests_Today"]
        self.requests_limit: int = data["Request_Limit_Daily"]

    @property
    def active_sessions_remaining(self) -> int:
        """
        The amount of active sessions remaining.

        :type: int
        """
        return self.active_sessions_limit - self.active_sessions_used

    @property
    def sessions_remaining(self) -> int:
        """
        The amount of sessions remaining.

        :type: int
        """
        return self.sessions_limit - self.sessions_used

    @property
    def requests_remaining(self) -> int:
        """
        The amount of requests remaining.

        :type: int
        """
        return self.requests_limit - self.requests_used

    @property
    def active_sessions_usage(self) -> float:
        """
        The percentage of active sessions used.

        :type: float
        """
        return self.active_sessions_used / self.active_sessions_limit

    @property
    def sessions_usage(self) -> float:
        """
        The percentage of sessions used.

        :type: float
        """
        return self.sessions_used / self.sessions_limit

    @property
    def requests_usage(self) -> float:
        """
        The percentage of requests used.

        :type: float
        """
        return self.requests_used / self.requests_limit

    @property
    def active_sessions_remaining_usage(self) -> float:
        """
        The percentage of active sessions remaining.

        :type: float
        """
        return self.active_sessions_remaining / self.active_sessions_limit

    @property
    def sessions_remaining_usage(self) -> float:
        """
        The percentage of sessions remaining.

        :type: float
        """
        return self.sessions_remaining / self.sessions_limit

    @property
    def requests_remaining_usage(self) -> float:
        """
        The percentage of requests remaining.

        :type: float
        """
        return self.requests_remaining / self.requests_limit


class Stats(WinLoseMixin):
    """
    Represents casual player stats.

    You can find these on the `Player.casual` attribute.

    Attributes
    ----------
    wins : int
        The amount of wins.
    losses : int
        The amount of losses.
    leaves : int
        The amount of times player left / disconnected from a match.
    """
    def __init__(self, stats_data: Union[responses.PlayerObject, responses.RankedStatsObject]):
        super().__init__(
            wins=stats_data["Wins"],
            losses=stats_data["Losses"],
        )
        self.leaves = stats_data["Leaves"]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.wins}/{self.losses} ({self.winrate_text})"


class RankedStats(Stats):
    """
    Represents ranked player stats.

    You can find these on the `Player.ranked_keyboard` and `Player.ranked_controller` attributes.

    Attributes
    ----------
    type : Literal["Keyboard", "Controller"]
        The type of these stats.
    wins : int
        The amount of wins.
    losses : int
        The amount of losses.
    leaves : int
        The amount of times player left / disconnected from a match.
    rank : Rank
        The player's current rank.
    points : int
        The amout of TP the player currently has.
    season : int
        The current ranked season.
    """
    def __init__(
        self, type_name: Literal["Keyboard", "Controller"], stats_data: responses.RankedStatsObject
    ):
        super().__init__(stats_data)
        self.type = type_name
        self.rank = Rank(stats_data["Tier"])
        self.season = stats_data["Season"]
        self.points = stats_data["Points"]
        # self.mmr = stats_data["Rank"]
        # self.prev_mmr = stats_data["PrevRank"]
        # self.trend = stats_data["Trend"]


class ChampionStats(WinLoseMixin, KDAMixin):
    """
    Represents player's champion stats.

    You can get these from the `PartialPlayer.get_champion_stats` method.

    Attributes
    ----------
    wins : int
        The amount of wins with this champion.
    losses : int
        The amount of losses with this champion.
    kills : int
        The amount of kills with this champion.
    deaths : int
        The amount of deaths with this champion.
    assists : int
        The amount of assists with this champion.
    player : Union[PartialPlayer, Player]
        The player these stats are for.
    champion : Union[Champion, CacheObject]
        The champion these stats are for.\n
        With incomplete cache, this will be a `CacheObject` with the name and ID set.
    queue : Optional[Queue]
        The queue these starts are for.\n
        `None` means these stats are for all queues.
    level : int
        The champion's mastery level.\n
        Will be ``0`` if these stats represent a single queue only.
    experience : int
        The amount of experience this champion has.
        Will be ``0`` if these stats represent a single queue only.
    last_played : datetime.datetime
        A timestamp of when this champion was last played,
        either in the given queue, or across all queues.
    credits : int
        The amount of credits earned by playing this champion.
    playtime : Duration
        The amount of time spent on playing this champion.
    """
    def __init__(
        self,
        player: Union[PartialPlayer, Player],
        cache_entry: Optional[CacheEntry],
        stats_data: Union[responses.ChampionRankObject, responses.ChampionQueueRankObject],
        queue: Optional[Queue] = None,
    ):
        WinLoseMixin.__init__(
            self,
            wins=stats_data["Wins"],
            losses=stats_data["Losses"],
        )
        KDAMixin.__init__(
            self,
            kills=stats_data["Kills"],
            deaths=stats_data["Deaths"],
            assists=stats_data["Assists"],
        )
        self.player: Union[PartialPlayer, Player] = player
        self.queue: Optional[Queue] = queue
        if queue is None:
            stats_data = cast(responses.ChampionRankObject, stats_data)
            champion_id = int(stats_data["champion_id"])
            champion_name = stats_data["champion"]
        else:
            stats_data = cast(responses.ChampionQueueRankObject, stats_data)
            champion_id = int(stats_data["ChampionId"])
            champion_name = stats_data["Champion"]
        champion: Optional[Union[Champion, CacheObject]] = None
        if cache_entry is not None:
            champion = cache_entry.champions.get(champion_id)
        if champion is None:
            champion = CacheObject(id=champion_id, name=champion_name)
        self.champion: Union[Champion, CacheObject] = champion
        self.last_played: datetime = _convert_timestamp(stats_data["LastPlayed"])
        self.level = stats_data.get("Rank", 0)
        self.experience = stats_data.get("Worshippers", 0)
        self.credits_earned = stats_data["Gold"]
        self.playtime = Duration(minutes=stats_data["Minutes"])
        # "MinionKills"  # kills_bot

    def __repr__(self) -> str:
        return f"{self.champion.name}({self.level}): ({self.wins}/{self.losses}) {self.kda_text}"
