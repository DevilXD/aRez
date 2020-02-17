from .utils import Duration
from typing import Union, Literal, TYPE_CHECKING

from .utils import convert_timestamp
from .enumerations import Rank, Language
from .mixins import WinLoseMixin, KDAMixin

if TYPE_CHECKING:
    from .player import PartialPlayer, Player  # noqa


class Stats(WinLoseMixin):
    """
    Represents casual player stats.

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
        return "{0.__class__.__name__}: {0.wins}/{0.losses} ({0.winrate_text})".format(self)


class RankedStats(Stats):
    """
    Represents ranked player stats.

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
    level : int
        The champion's mastery level.
    last_played : datetime.datetime
        A timestamp of when this champion was last played.
    experience : int
        The amount of experience this champion has.
    credits : int
        The amount of credits earned by playing this champion.
    playtime : Duration
        The amount of time spent on playing this champion.
    """
    def __init__(
        self, player: Union["PartialPlayer", "Player"], language: Language, stats_data: dict
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
        self.champion = self.player._api.get_champion(int(stats_data["champion_id"]), language)
        self.last_played = convert_timestamp(stats_data["LastPlayed"])
        self.level = stats_data["Rank"]
        self.experience = stats_data["Worshippers"]
        self.credits_earned = stats_data["Gold"]
        self.playtime = Duration(minutes=stats_data["Minutes"])
        # "MinionKills"

    def __repr__(self) -> str:
        champion_name = self.champion.name if self.champion is not None else "Unknown"
        return "{1}({0.level}): ({0.wins}/{0.losses}) {0.kda_text}".format(self, champion_name)
