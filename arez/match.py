from __future__ import annotations

import logging
from itertools import count
from typing import Any, Optional, Union, List, Dict, Generator, TYPE_CHECKING

from .exceptions import NotFound
from .enumerations import Queue, Language, Region, Rank
from .mixins import APIClient, MatchMixin, MatchPlayerMixin, Expandable, WinLoseMixin

if TYPE_CHECKING:  # pragma: no branch
    from .items import Device  # noqa
    from .api import PaladinsAPI
    from .champion import Champion
    from .player import PartialPlayer, Player  # noqa


__all__ = [
    "PartialMatch",
    "MatchPlayer",
    "Match",
    "LivePlayer",
    "LiveMatch",
]
logger = logging.getLogger(__package__)


class PartialMatch(MatchPlayerMixin, MatchMixin, Expandable):
    """
    Represents a match from a single player's perspective only.

    This partial object is returned by the `PartialPlayer.get_match_history` player's method.
    To obtain an object with all match information, try awaiting on this object like so:

    .. code-block:: py

        match = await partial_match

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
        The match's ending score.\n
        The first value is always the allied-team score, while the second one - enemy team score.
    winning_team : Literal[1, 2]
        The winning team of this match.
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
        The amount of kills.
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
        self, player: Union["PartialPlayer", "Player"], language: Language, match_data: dict
    ):
        MatchPlayerMixin.__init__(self, player, language, match_data)
        MatchMixin.__init__(self, match_data)
        self._language = language

    async def _expand(self) -> Optional[Match]:
        """
        Upgrades this object into a full `Match` one, containing all match players and information.

        Uses up a single request.

        Returns
        -------
        Match
            The full match object.

        Raises
        ------
        NotFound
            The match could not be found.
        """
        logger.info(f"PartialMatch(id={self.id}).expand()")
        response = await self._api.request("getmatchdetails", self.id)
        if not response:
            raise NotFound("Match")
        return Match(self._api, self._language, response, {})

    def __repr__(self) -> str:
        champion_name = self.champion.name if self.champion is not None else "Unknown"
        return f"{self.queue.name}: {champion_name}: {self.kda_text}"

    @property
    def disconnected(self) -> bool:
        """
        Returns `True` if the player has disconnected during the match, `False` otherwise.\n
        This is done by checking if either `damage_bot` or `healing_bot` are non zero.

        :type: bool
        """
        return self.damage_bot > 0 or self.healing_bot > 0


class MatchPlayer(MatchPlayerMixin):
    """
    Represents a full match's player.

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
    points_captured : int
        The amount of times the player's team captured the point.\n
        This is ``0`` for non-Siege matches.
    push_successes : int
        The amount of times the player's team successfully pushed the payload to the end.\n
        This is ``0`` for non-Siege matches.
    kills_bot : int
        The amount of bot kills.
    account_level : int
        The player's account level.
    mastery_level : int
        The player's champion mastery level.
    party_number : int
        A number denoting the party the player belonged to.\n
        ``0`` means the player wasn't in a party.
    """
    def __init__(
        self,
        api: "PaladinsAPI",
        language: Language,
        player_data: Dict[str, Any],
        parties: Dict[int, int],
        players: Dict[int, Player],
    ):
        player: Optional[Union[PartialPlayer, Player]] = players.get(int(player_data["playerId"]))
        if player is None:
            # if no full player was found
            from .player import PartialPlayer  # noqa, cyclic imports
            player = PartialPlayer(
                api,
                id=player_data["playerId"],
                name=player_data["playerName"],
                platform=player_data["playerPortalId"],
            )
        super().__init__(player, language, player_data)
        self.points_captured: int = player_data["Kills_Gold_Fury"]
        self.push_successes: int = player_data["Kills_Fire_Giant"]
        self.kills_bot: int  = player_data["Kills_Bot"]
        self.account_level: int = player_data["Account_Level"]
        self.mastery_level: int = player_data["Mastery_Level"]
        self.party_number: int = parties.get(player_data["PartyId"], 0)

    @property
    def disconnected(self) -> bool:
        """
        Returns `True` if the player has disconnected during the match, `False` otherwise.\n
        This is done by checking if either `damage_bot` or `healing_bot` are non zero.

        :type: bool
        """
        return self.damage_bot > 0 or self.healing_bot > 0

    def __repr__(self) -> str:
        player_name = self.player.name if self.player.id else "Unknown"
        return (
            f"{player_name}({self.player.id}): "
            f"({self.kda_text}, {self.damage_done}, {self.healing_done})"
        )


class Match(APIClient, MatchMixin):
    """
    Represents already-played full match information.
    You can get this from the `PaladinsAPI.get_match` and `PaladinsAPI.get_matches` methods,
    as well as from upgrading a `PartialMatch` object.

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
        The match's ending score.\n
        The first value is the ``team1`` score, while the second value - ``team2`` score.
    winning_team : Literal[1, 2]
        The winning team of this match.
    replay_available : bool
        `True` if this match has a replay that you can watch, `False` otherwise.
    bans : List[Champion]
        A list of champions banned in this match.\n
        This is an empty list for non-ranked matches, or with incomplete cache.
    team1 : List[MatchPlayer]
        A list of players in the first team.
    team2 : List[MatchPlayer]
        A list of players in the second team.
    players : Generator[MatchPlayer]
        A generator that iterates over all match players in the match.
    """
    def __init__(
        self,
        api: "PaladinsAPI",
        language: Language,
        match_data: List[Dict[str, Any]],
        players: Dict[int, Player],
    ):
        APIClient.__init__(self, api)
        first_player = match_data[0]
        MatchMixin.__init__(self, first_player)
        logger.debug(f"Match(id={self.id}) -> creating...")
        self.replay_available: bool = first_player["hasReplay"] == "y"
        self.bans: List[Champion] = []
        for i in range(1, 5):
            ban_id = first_player[f"BanId{i}"]
            if not ban_id:
                continue
            ban_champ = self._api.get_champion(ban_id, language)
            if ban_champ:  # pragma: no branch  # TODO: Use the walrus operator here
                self.bans.append(ban_champ)
        self.team1: List[MatchPlayer] = []
        self.team2: List[MatchPlayer] = []
        # We need to do this here because apparently one-man parties are a thing
        party_count = count(1)
        parties: Dict[int, int] = {}
        for player_data in match_data:
            pid = player_data["PartyId"]
            if not pid:
                # skip 0s
                continue
            if pid not in parties:
                # haven't seen this one yet, assign zero
                parties[pid] = 0
            elif parties[pid] == 0:
                # we've seen this one, and it doesn't have a number assigned - assign one
                parties[pid] = next(party_count)
            match_player = MatchPlayer(self._api, language, player_data, parties, players)
            team_number = player_data['TaskForce']
            if team_number == 1:
                self.team1.append(match_player)
            elif team_number == 2:  # pragma: no branch
                self.team2.append(match_player)
        logger.debug(f"Match(id={self.id}) -> created")

    @property
    def players(self) -> Generator[MatchPlayer, None, None]:
        for p in self.team1:
            yield p
        for p in self.team2:
            yield p

    def __repr__(self) -> str:
        return f"{self.queue.name}({self.id}): {self.score}"

    async def expand_players(self):
        """
        Makes partial player objects in the containing match player objects be expanded into
        full `Player` objects, if possible.

        Uses up a single request to do the expansion.
        """
        players = await self._api.get_players((p.player.id for p in self.players))
        players_dict = {p.id: p for p in players}
        for mp in self.players:
            pid = mp.player.id
            if not pid:
                # skip 0s
                continue
            p = players_dict.get(pid)
            if p is not None:  # TODO: (maybe) use a walrus operator here
                mp.player = p


class LivePlayer(APIClient, WinLoseMixin):
    """
    Represents a live match player.
    You can find these on the `LiveMatch.team1` and `LiveMatch.team2` attributes.

    Attributes
    ----------
    player : Union[PartialPlayer, Player]
        The actual player playing in this match.
    champion : Optional[Champion]
        The champion the player is using in this match.\n
        `None` with incomplete cache.
    rank : Rank
        The player's rank.
    account_level : int
        The player's account level.
    mastery_level : int
        The player's champion mastery level.
    wins : int
        The amount of wins.
    losses : int
        The amount of losses.
    """
    def __init__(
        self,
        api: "PaladinsAPI",
        language: Language,
        player_data: Dict[str, Any],
        players: Dict[int, Player],
    ):
        APIClient.__init__(self, api)
        WinLoseMixin.__init__(
            self,
            wins=player_data["tierWins"],
            losses=player_data["tierLosses"],
        )
        player: Optional[Union[PartialPlayer, Player]] = players.get(int(player_data["playerId"]))
        if player is None:
            # if no full player was found
            from .player import PartialPlayer  # noqa, cyclic imports
            player = PartialPlayer(
                api, id=player_data["playerId"], name=player_data["playerName"]
            )
        self.player: Union[PartialPlayer, Player] = player
        self.champion: Optional[Champion] = self._api.get_champion(
            player_data["ChampionId"], language
        )
        self.rank = Rank(player_data["Tier"], return_default=True)
        self.account_level: int = player_data["Account_Level"]
        self.mastery_level: int = player_data["Mastery_Level"]

    def __repr__(self) -> str:
        player_name = self.player.name if self.player.id else "Unknown"
        champion_name = self.champion.name if self.champion is not None else "Unknown"
        return (
            f"{player_name}({self.player.id}): "
            f"{self.account_level} level: "
            f"{champion_name}({self.mastery_level})"
        )


class LiveMatch(APIClient):
    """
    Represents an on-going live match.
    You can get this from the `PlayerStatus.get_live_match` method.

    Attributes
    ----------
    id : int
        The match ID.
    map_name : str
        The name of the map played.
    queue : Queue
        The queue the match is being played in.
    region : Region
        The region this match is being played in.
    team1 : List[LivePlayer]
        A list of live players in the first team.
    team2 : List[LivePlayer]
        A list of live players in the second team.
    players : Generator[LivePlayer]
        A generator that iterates over all live match players in the match.
    """
    def __init__(
        self,
        api: "PaladinsAPI",
        language: Language,
        match_data: List[dict],
        players: Dict[int, Player],
    ):
        super().__init__(api)
        first_player = match_data[0]
        self.id: int = first_player["Match"]
        self.map_name: str = first_player["mapGame"]
        self.queue = Queue(int(first_player["Queue"]), return_default=True)
        self.region = Region(first_player["playerRegion"], return_default=True)
        self.team1: List[LivePlayer] = []
        self.team2: List[LivePlayer] = []
        for player_data in match_data:
            live_player = LivePlayer(self._api, language, player_data, players)
            if player_data["taskForce"] == 1:
                self.team1.append(live_player)
            elif player_data["taskForce"] == 2:  # pragma: no branch
                self.team2.append(live_player)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.queue.name}): {self.map_name}"

    @property
    def players(self) -> Generator[LivePlayer, None, None]:
        for p in self.team1:
            yield p
        for p in self.team2:
            yield p

    async def expand_players(self):
        """
        Makes partial player objects in the containing match player objects be expanded into
        full `Player` objects, if possible.

        Uses up a single request to do the expansion.
        """
        players = await self._api.get_players((p.player.id for p in self.players))
        players_dict = {p.id: p for p in players}
        for mp in self.players:
            pid = mp.player.id
            if not pid:
                # skip 0s
                continue
            p = players_dict.get(pid)
            if p is not None:  # TODO: (maybe) use a walrus operator here
                mp.player = p
