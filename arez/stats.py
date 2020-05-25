from .utils import Duration
from typing import Optional, Union, Literal, TYPE_CHECKING

from .utils import convert_timestamp
from .mixins import WinLoseMixin, KDAMixin
from .enumerations import Rank, Language, Queue

if TYPE_CHECKING:  # pragma: no branch
    from .player import PartialPlayer, Player  # noqa


__all__ = [
    "Stats",
    "RankedStats",
    "ChampionStats",
]


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
    def __init__(self, stats_data: dict):
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
    def __init__(self, type_name: Literal["Keyboard", "Controller"], stats_data: dict):
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

    You can find these from the `PartialPlayer.get_champion_stats` method.

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
    champion : Optional[Champion]
        The champion these stats are for.\n
        `None` for incomplete cache.
    queue : Queue
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
        player: Union["PartialPlayer", "Player"],
        language: Language,
        stats_data: dict,
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
        self.player = player
        self.queue = queue
        if queue is None:
            champion_id = int(stats_data["champion_id"])
        else:
            champion_id = int(stats_data['ChampionId'])
        self.champion = self.player._api.get_champion(champion_id, language)
        self.last_played = convert_timestamp(stats_data["LastPlayed"])
        self.level = stats_data.get("Rank", 0)
        self.experience = stats_data.get("Worshippers", 0)
        self.credits_earned = stats_data["Gold"]
        self.playtime = Duration(minutes=stats_data["Minutes"])
        # "MinionKills"

    def __repr__(self) -> str:
        champion_name = self.champion.name if self.champion is not None else "Unknown"
        return f"{champion_name}({self.level}): ({self.wins}/{self.losses}) {self.kda_text}"
