from math import nan
from enum import Enum
from typing import Union

class WinLoseMixin:
    def __init__(self, stats_data: dict):
        self.wins = stats_data["Wins"]
        self.losses = stats_data["Losses"]
    
    @property
    def matches_played(self) -> int:
        return self.wins + self.losses
    
    @property
    def winrate(self) -> Union[str, float]:
        return self.wins / self.matches_played if self.matches_played > 0 else nan
    
    @property
    def winrate_text(self) -> str:
        return "{}%".format(round(self.winrate * 100, 3)) if self.matches_played > 0 else "N/A"

class KDAMixin:
    def __init__(self, stats_data: dict):
        self.kills = stats_data["Kills"]
        self.deaths = stats_data["Deaths"]
        self.assists = stats_data["Assists"]
    
    @property
    def kda(self) -> int:
        return (self.kills + self.assists / 2) / self.deaths if self.deaths > 0 else nan

    @property
    def kda_text(self) -> str:
        return "{0.kills}/{0.deaths}/{0.assists}".format(self)