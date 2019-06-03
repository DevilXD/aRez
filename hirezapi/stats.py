from typing import Union
from datetime import timedelta

from .utils import convert_timestamp
from .enumerations import Rank, Language
from .mixins import WinLoseMixin, KDAMixin

class Stats(WinLoseMixin):
    def __init__(self, stats_data: dict):
        super().__init__(stats_data)
        self.leaves = stats_data["Leaves"]
    
    def __repr__(self) -> str:
        return "{self.__class__.__name__}: {self.wins}/{self.losses} ({0.winrate_text})".format(self)

class RankedStats(Stats):
    def __init__(self, stats_data: dict):
        super().__init__(stats_data)
        self.rank = Rank(stats_data["Tier"])
        self.season = stats_data["Season"]
        self.points = stats_data["Points"]
        self.mmr = stats_data["Rank"]
        self.prev_mmr = stats_data["PrevRank"]
        self.trend = stats_data["Trend"]

class ChampionStats(WinLoseMixin, KDAMixin):
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
        self.playtime = timedelta(minutes=stats_data["Minutes"])
        #"MinionKills"
    
    def __repr__(self) -> str:
        return "{0.champion.name}({0.level}): ({0.wins}/{0.losses}) {0.kda_text}".format(self)
