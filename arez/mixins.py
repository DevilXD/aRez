from math import nan
from abc import ABC, abstractmethod
from typing import Optional, Union, List, Tuple, Literal, TYPE_CHECKING

from .utils import convert_timestamp, Duration
from .enumerations import Language, Queue, Region

if TYPE_CHECKING:
    from .api import PaladinsAPI
    from .champion import Champion
    from .player import PartialPlayer, Player


__all__ = [
    "APIClient",
    "Expandable",
    "WinLoseMixin",
    "KDAMixin",
    "MatchMixin",
    "MatchPlayerMixin",
]


class APIClient:
    """
    Abstract base class that has to be met by most (if not all) objects that interact with the API.

    Provides access to the core of this wrapper, that is the `.request` method and `.get_*`
    methods from the cache system.
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
        setattr(cls, "__await__", __await__)

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
    def __init__(self, match_data: dict):
        self.id: int = match_data["Match"]
        if "hasReplay" in match_data:
            # we're in a full match data
            stamp = match_data["Entry_Datetime"]
            queue = match_data["match_queue_id"]
            score = (match_data["Team1Score"], match_data["Team2Score"])
        else:
            # we're in a partial (player history) match data
            stamp = match_data["Match_Time"]
            queue = match_data["Match_Queue_Id"]
            my_team = match_data["TaskForce"]
            other_team = 1 if my_team == 2 else 2
            score = (
                match_data[f"Team{my_team}Score"],
                match_data[f"Team{other_team}Score"],
            )
        self.queue = Queue(queue, return_default=True)
        self.region = Region(match_data["Region"], return_default=True)
        self.timestamp = convert_timestamp(stamp)
        self.duration = Duration(seconds=match_data["Time_In_Match_Seconds"])
        self.map_name: str = match_data["Map_Game"]
        if self.queue in (469, 470):
            # Score correction for TDM matches
            score = (score[0] + 36, score[1] + 36)
        self.score: Tuple[int, int] = score
        self.winning_team: Literal[1, 2] = match_data["Winning_TaskForce"]


class MatchPlayerMixin(APIClient, KDAMixin):
    """
    Represents basic information about a player in a match.

    Attributes
    ----------
    player : Union[PartialPlayer, Player]
        The player who participated in this match.\n
        This is usually a new partial player object.\n
        All attributes, Name, ID and Platform, should be present.
    champion : Optional[Champion]
        The champion used by the player in this match.\n
        `None` with incomplete cache.
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
    team_number : Literal[1, 2]
        The team this player belongs to.
    team_score : int
        The score of the player's team.
    winner : bool
        `True` if the player won this match, `False` otherwise.
    """
    def __init__(
        self, player: Union["Player", "PartialPlayer"], language: Language, match_data: dict
    ):
        APIClient.__init__(self, player._api)
        if "hasReplay" in match_data:
            # we're in a full match data
            creds = match_data["Gold_Earned"]
            kills = match_data["Kills_Player"]
            damage = match_data["Damage_Done_Physical"]
        else:
            # we're in a partial (player history) match data
            creds = match_data["Gold"]
            kills = match_data["Kills"]
            damage = match_data["Damage"]
        KDAMixin.__init__(
            self, kills=kills, deaths=match_data["Deaths"], assists=match_data["Assists"]
        )
        self.player: Union[Player, PartialPlayer] = player
        self.champion: Optional[Champion] = self._api.get_champion(
            match_data["ChampionId"], language
        )
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
        # self.skin  # TODO: Ask for this to be added/fixed properly
        self.team_number: Literal[1, 2] = match_data["TaskForce"]
        self.team_score: int = match_data[f"Team{self.team_number}Score"]
        self.winner: bool = self.team_number == match_data["Winning_TaskForce"]

        from .items import MatchLoadout, MatchItem  # cyclic imports
        self.items: List[MatchItem] = []
        for i in range(1, 5):
            item_id = match_data[f"ActiveId{i}"]
            if not item_id:
                continue
            item = self._api.get_item(item_id, language)
            level = match_data[f"ActiveLevel{i}"] // 4 + 1
            self.items.append(MatchItem(item, level))
        self.loadout = MatchLoadout(self._api, language, match_data)

    @property
    def shielding(self) -> int:
        """
        This is an alias for the `damage_mitigated` attribute.

        :type: int
        """
        return self.damage_mitigated
