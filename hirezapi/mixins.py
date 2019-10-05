from math import nan

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
    """
    def __init__(self, *, kills: int, deaths: int, assists: int):
        self.kills = kills
        self.deaths = deaths
        self.assists = assists
    
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
    def kda_text(self) -> str:
        """
        Kills, deaths and assists as a slash-delimited string.\n
        The format is: ``kills/deaths/assists``, or ``1/2/3``.
        
        :type: str
        """
        return "{0.kills}/{0.deaths}/{0.assists}".format(self)