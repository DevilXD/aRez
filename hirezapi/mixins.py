from math import nan
from enum import Enum
from typing import Union

class WinLoseMixin:
    """
    Represents player's wins and losses. Contains useful helper attributes.
    
    Attributes
    ----------
    wins : int
        The amount of wins.
    losses : int
        The amount of losses.
    matches_played : int
        The amount of matches played. This is just `wins + losses`.
    winrate : float
        The calculated winrate as a fraction.
        NaN is returned if there was no matches played.
    winrate_text : str
        The calculated winrate as a percentage string.
        The format is: `48.213%`
        `"N/A"` is returned if there was no matches played.
    """
    def __init__(self, stats_data: dict):
        self.wins = stats_data["Wins"]
        self.losses = stats_data["Losses"]
    
    @property
    def matches_played(self) -> int:
        return self.wins + self.losses
    
    @property
    def winrate(self) -> float:
        return self.wins / self.matches_played if self.matches_played > 0 else nan
    
    @property
    def winrate_text(self) -> str:
        return "{}%".format(round(self.winrate * 100, 3)) if self.matches_played > 0 else "N/A"

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
    kda : float
        The calculated KDA.
        The formula is: `(kills + assists / 2) / deaths`.
        NaN is returned if there was no deaths.
    kda_text : str
        The calculated KDA as a `/` delimited string.
        The format is: `kills/deaths/assists`, or `1/2/3`.
    """
    def __init__(self, stats_data: dict):
        self.kills = stats_data["Kills"]
        self.deaths = stats_data["Deaths"]
        self.assists = stats_data["Assists"]
    
    @property
    def kda(self) -> float:
        return (self.kills + self.assists / 2) / self.deaths if self.deaths > 0 else nan

    @property
    def kda_text(self) -> str:
        return "{0.kills}/{0.deaths}/{0.assists}".format(self)