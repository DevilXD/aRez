from typing import Union
from .utils import Duration

from .utils import convert_timestamp
from .enumerations import Rank, Language
from .mixins import WinLoseMixin, KDAMixin

class Stats(WinLoseMixin):
    """
    Represents casual player stats.
    
    Attributes
    ----------
    leaves : int
        The amount of times player left / disconnected from a match.
    """
    def __init__(self, stats_data: dict):
        super().__init__(stats_data)
        self.leaves = stats_data["Leaves"]
    
    def __repr__(self) -> str:
        return "{self.__class__.__name__}: {self.wins}/{self.losses} ({0.winrate_text})".format(self)

class RankedStats(Stats):
    """
    Represents ranked player stats.
    
    Attributes
    ----------
    rank : Rank
        The player's current rank.
    points : int
        The amout of TP the player currrently has.
    season : int
        The current ranked season.
    mmr : int
        The current MMR of the player.
        This is currently always returned as 0 by the API.
        Not useable.
    prev_mmr : int
        The previous MMR of the player.
        This is currently always returned as 0 by the API.
        Not useable.
    trend : int
        The player's MMR trend.
        This is currently always returned as 0 by the API.
        Not useable.
    """
    def __init__(self, stats_data: dict):
        super().__init__(stats_data)
        self.rank = Rank(stats_data["Tier"])
        self.season = stats_data["Season"]
        self.points = stats_data["Points"]
        self.mmr = stats_data["Rank"]
        self.prev_mmr = stats_data["PrevRank"]
        self.trend = stats_data["Trend"]

class ChampionStats(WinLoseMixin, KDAMixin):
    """
    Represents player's champion stats.
    
    Attributes
    ----------
    player : Union[PartialPlayer, Player]
        The player the stats are for.
    langage : Language
        The langauge the stats are in.
    champion : Champion
        The champion the stats are for.
    level : int
        The champion's mastery level.
    last_played : datetime
        A timestamp of when this champion was last played.
    experience : int
        The amount of experience this champion has.
    credits : int
        The amount of credits earned by playing this champion.
    playtime : Duration
        The amount of time spent playing this champion.
    """
    def __init__(self, player: Union['PartialPlayer', 'Player'], language: Language, stats_data: dict):
        super().__init__(stats_data)
        super(WinLoseMixin, self).__init__(stats_data) #pylint: disable=bad-super-call
        self.player = player
        self.language = language
        self.champion = self.player._api.get_champion(int(stats_data["champion_id"]), language)
        self.last_played = convert_timestamp(stats_data["LastPlayed"])
        self.level = stats_data["Rank"]
        self.experience = stats_data["Worshippers"]
        self.credits_earned = stats_data["Gold"]
        self.playtime = Duration(minutes=stats_data["Minutes"])
        #"MinionKills"
    
    def __repr__(self) -> str:
        return "{0.champion.name}({0.level}): ({0.wins}/{0.losses}) {0.kda_text}".format(self)
