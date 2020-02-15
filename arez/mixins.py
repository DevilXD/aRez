from math import nan
from abc import ABC, abstractmethod
from typing import Optional, Union, List, Literal, TYPE_CHECKING


if TYPE_CHECKING:
    from .api import PaladinsAPI
    from .champion import Champion
    from .enumerations import Language
    from .player import PartialPlayer, Player
    from .match import MatchLoadout, MatchItem


class APIClient:
    """
    Abstract base class that has to be met by most (if not all) objects.

    Provides access to the core of this wrapper, that is the `.request` method and `.get_*`
    from the cache system.
    """
    def __init__(self, api: "PaladinsAPI"):
        self._api = api


class Expandable(ABC):
    """
    An abstract class that can be used to make partial objects "expandable" to their full version.

    Subclasses should overwrite the `_expand` method with proper implementation, returning
    the full expanded object.
    """
    # Subclasses will have their `_expand` method doc linked as the `__await__` doc.
    def __init_subclass__(cls):
        # Create a new await method
        def __await__(self):
            return self._expand().__await__()
        # Copy over the docstring
        __await__.__doc__ = cls._expand.__doc__
        # Attach the method to the subclass
        cls.__await__ = __await__

    def __await__(self):
        return self._expand().__await__()

    @abstractmethod
    async def _expand(self):
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
