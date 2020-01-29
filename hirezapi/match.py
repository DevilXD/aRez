from typing import Optional, Union, List, Tuple, Literal, Generator, TYPE_CHECKING

from .items import LoadoutCard
from .mixins import KDAMixin, WinLoseMixin
from .utils import convert_timestamp, Duration
from .enumerations import Queue, Language, Region, Rank

if TYPE_CHECKING:
    from .items import Device  # noqa
    from .api import PaladinsAPI
    from .champion import Champion
    from .player import PartialPlayer, Player  # noqa


class MatchItem:
    """
    Represents an item shop's purchase.

    Attributes
    ----------
    item : Optional[Device]
        The purchased item.\n
        `None` with incomplete cache.
    level : int
        The level of the item purchased.
    """
    def __init__(self, item, level):
        self.item: Optional["Device"] = item
        self.level: int = level

    def __repr__(self) -> str:
        item_name = self.item.name if self.item else "Unknown"
        return "{1}: {0.level}".format(self, item_name)


class MatchLoadout:
    """
    Represents a loadout used in a match.

    Attributes
    ----------
    cards : List[LoadoutCard]
        A list of loadout cards used.\n
        Can be empty if the player haven't picked a loadout during the match.
    talent : Optional[Device]
        The talent used.\n
        `None` when the player haven't picked a talent during the match, or with incomplete cache.
    """
    def __init__(self, api, language: Language, match_data: dict):
        self.cards = []
        for i in range(1, 6):
            card_id = match_data["ItemId{}".format(i)]
            if not card_id:
                continue
            self.cards.append(
                LoadoutCard(
                    api.get_card(card_id, language),
                    match_data["ItemLevel{}".format(i)]
                )
            )
        self.cards.sort(key=lambda c: c.points, reverse=True)
        self.talent = api.get_talent(match_data["ItemId6"], language)

    def __repr__(self) -> str:
        if self.cards:
            talent_name = self.talent.name if self.talent else "Unknown"
            return "{}: {}/{}/{}/{}/{}".format(talent_name, *(c.points for c in self.cards))
        else:
            # This can happen if the player haven't picked a talent / loadout during the match
            return "No Loadout"


class PartialMatch(KDAMixin):
    """
    Represents a match from a single player's perspective only.

    This partial object is returned by the `get_match_history` player's method.
    To obtain a full object, try using `expand`.

    Attributes
    ----------
    id : int
        The match ID.
    player : Union[PartialPlayer, Player]
        The player this match is for.
    language : Language
        The language of cards, talents and items this match has.
    champion : Optional[Champion]
        The champion used by the player in this match.\n
        `None` with incomplete cache.
    queue : Queue
        The queue this match was played in.
    region : Region
        The region this match was played in.
    timestamp : datetime
        A timestamp of when this match happened.
    duration : Duration
        The duration of the match.
    map_name : str
        The name of the map played.
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
    damage_dealt : int
        The amount of damage dealt.
    damage_taken : int
        The amount of damage taken.
    damage_mitigated : int
        The amount of damage mitigated (shielding).
    damage_bot : int
        The amount of damage done by the player's bot after they disconnected.
    healing_done : int
        The amount of healing done to other players.
    healing_self : int
        The amount of healing done to self.
    healing_bot : int
        The amount of healing done by the player's bot after they disconnected.
    objective_time : int
        The amount of objective time the player got, in seconds.
    multikill_max : int
        The maximum multikill player did during the match.
    score : Tuple[int, int]
        The match's ending score. The first value is always the allied-team score,
        while the second one - enemy team score.
    win_status : bool
        `True` if the player won this match, `False` otherwise.
    """
    def __init__(
        self, player: Union["PartialPlayer", "Player"], language: Language, match_data: dict
    ):
        super().__init__(
            kills=match_data["Kills"],
            deaths=match_data["Deaths"],
            assists=match_data["Assists"],
        )
        self._api: "PaladinsAPI" = player._api
        self.player = player
        self.language = language
        self.id: int = match_data["Match"]
        self.champion: Optional[Champion] = self._api.get_champion(
            match_data["ChampionId"], language
        )
        self.queue = Queue.get(match_data["Match_Queue_Id"]) or Queue(0)
        self.region = Region.get(match_data["Region"]) or Region(0)
        self.duration = Duration(seconds=match_data["Time_In_Match_Seconds"])
        self.timestamp = convert_timestamp(match_data["Match_Time"])
        self.map_name: str = match_data["Map_Game"]

        self.credits: int = match_data["Gold"]
        self.damage_dealt: int = match_data["Damage"]
        self.damage_taken: int = match_data["Damage_Taken"]
        self.damage_mitigated: int = match_data["Damage_Mitigated"]
        self.damage_bot: int = match_data["Damage_Bot"]
        self.healing_done: int = match_data["Healing"]
        self.healing_self: int = match_data["Healing_Player_Self"]
        self.healing_bot: int = match_data["Healing_Bot"]

        self.objective_time = match_data["Objective_Assists"]
        self.multikill_max  = match_data["Multi_kill_Max"]

        my_team = match_data["TaskForce"]
        my_score = match_data["Team{}Score".format(my_team)]
        other_team = 1 if my_team == 2 else 2
        other_score = match_data["Team{}Score".format(other_team)]
        self.score: Tuple[int, int] = (my_score, other_score)
        self.win_status = my_team == match_data["Winning_TaskForce"]

        self.items: List[MatchItem] = []
        for i in range(1, 5):
            item_id = match_data["ActiveId{}".format(i)]
            if not item_id:
                continue
            item = self._api.get_item(item_id, language)
            level = match_data["ActiveLevel{}".format(i)] // 4 + 1
            self.items.append(MatchItem(item, level))
        self.loadout = MatchLoadout(self._api, language, match_data)

    def __repr__(self) -> str:
        champion_name = self.champion.name if self.champion is not None else "Unknown"
        return "{0.queue.name}: {1}: {0.kda_text}".format(self, champion_name)

    @property
    def disconnected(self) -> bool:
        """
        Checks if the player has disconnected during the match.
        This is done by checking if either `damage_bot` or `healing_bot` are non zero.

        Returns
        -------
        bool
            `True` if the player got disconnected, `False` otherwise.
        """
        return self.damage_bot > 0 or self.healing_bot > 0

    async def expand(self) -> 'Match':
        """
        Expands this object into a full Match, containing all match players and information.

        Returns
        -------
        Match
            The expanded match object.
        """
        response = await self._api.request("getmatchdetails", self.id)
        return Match(self._api, self.language, response)


class MatchPlayer(KDAMixin):
    """
    Represents a full match's player.

    Attributes
    ----------
    player : PartialPlayer
        The player who participated in this match.
        This is always a new, partial object, regardless of which way the match was fetched.
        All attributes, Name, ID and Platform, should be present.
    champion : Optional[Champion]
        The champion used by the player in this match.\n
        `None` with incomplete cache.
    loadout : MatchLoadout
        The loadout used by the player in this match.
    account_level : int
        The player's account level.
    mastery_level : int
        The player's champion mastery level.
    items : List[MatchItem]
        A list of items bought by the player during this match.
    credits : int
        The amount of credits earned this match.
    kills : int
        The amount of player kills.
    kills_bot : int
        The amount of bot kills.
    deaths : int
        The amount of deaths.
    assists : int
        The amount of assists.
    damage_dealt : int
        The amount of damage dealt.
    damage_taken : int
        The amount of damage taken.
    damage_mitigated : int
        The amount of damage mitigated (shielding).
    damage_bot : int
        The amount of damage done by the player's bot after they disconnected.
    healing_done : int
        The amount of healing done to other players.
    healing_self : int
        The amount of healing done to self.
    healing_bot : int
        The amount of healing done by the player's bot after they disconnected.
    objective_time : int
        The amount of objective time the player got, in seconds.
    multikills : Tuple[int, int, int, int]
        The amount of (double, tripple, quadra, penta) kills the player did during the match.
    multikill_max : int
        The maximum multikill player did during the match.
    """
    def __init__(self, api: "PaladinsAPI", language: Language, player_data: dict):
        super().__init__(
            kills=player_data["Kills_Player"],
            deaths=player_data["Deaths"],
            assists=player_data["Assists"],
        )
        self._api = api
        from .player import PartialPlayer  # noqa, cyclic imports
        self.player = PartialPlayer(
            self._api,
            id=player_data["playerId"],
            name=player_data["playerName"],
            platform=player_data["playerPortalId"],
        )
        self.champion: Optional[Champion] = self._api.get_champion(
            player_data["ChampionId"], language
        )
        self.account_level: int = player_data["Account_Level"]
        self.mastery_level: int = player_data["Mastery_Level"]

        self.credits: int = player_data["Gold_Earned"]
        self.damage_dealt: int = player_data["Damage_Done_Physical"]
        self.damage_taken: int = player_data["Damage_Taken"]
        self.damage_mitigated: int = player_data["Damage_Mitigated"]
        self.damage_bot: int = player_data["Damage_Bot"]
        self.healing_done: int = player_data["Healing"]
        self.healing_self: int = player_data["Healing_Player_Self"]
        self.healing_bot: int = player_data["Healing_Bot"]

        self.kills_bot: int  = player_data["Kills_Bot"]
        self.objective_time: int = player_data["Objective_Assists"]
        self.multikill_max: int = player_data["Multi_kill_Max"]
        self.multikills: Tuple[int, int, int, int] = (
            player_data["Kills_Double"],
            player_data["Kills_Triple"],
            player_data["Kills_Quadra"],
            player_data["Kills_Penta"],
        )

        self.items: List[MatchItem] = []
        for i in range(1, 5):
            item_id = player_data["ActiveId{}".format(i)]
            if not item_id:
                continue
            item = self._api.get_item(item_id, language)
            level = player_data["ActiveLevel{}".format(i)] + 1
            self.items.append(MatchItem(item, level))
        self.loadout = MatchLoadout(self._api, language, player_data)

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
        return "{1}({0.player.id}): ({0.kda_text}, {0.damage_dealt}, {0.healing_done})".format(
            self, player_name
        )


class Match:
    """
    Represents an entire, full match.

    Attributes
    ----------
    id : int
        The match ID.
    language : Language
        The language of cards, talents and items this match has.
    queue : Queue
        The queue this match was played in.
    region : Region
        The region this match was played in.
    timestamp : datetime
        A timestamp of when this match happened.
    duration : Duration
        The duration of the match.
    bans : List[Champion]
        A list of champions banned this match.\n
        This is an empty list for non-ranked matches, or with incomplete cache.
    map_name : str
        The name of the map played.
    score : Tuple[int, int]
        The match's ending score.
        The first value is the ``team1`` score, while the second value - ``team2`` score.
    winning_team : Literal[1, 2]
        The winning team of this match.
    team1 : List[MatchPlayer]
        A list of players in the first team.
    team2 : List[MatchPlayer]
        A list of players in the second team.
    players : Generator[MatchPlayer]
        A generator that iterates over all match players in the match.
    """
    def __init__(self, api: "PaladinsAPI", language: Language, match_data: List[dict]):
        self._api = api
        self.language = language
        first_player = match_data[0]
        self.id: int = first_player["Match"]
        self.region = Region.get(first_player["Region"]) or Region(0)
        self.queue = Queue.get(first_player["match_queue_id"]) or Queue(0)
        self.map_name: str = first_player["Map_Game"]
        self.duration = Duration(seconds=first_player["Time_In_Match_Seconds"])
        self.timestamp = convert_timestamp(first_player["Entry_Datetime"])
        self.score: Tuple[int, int] = (first_player["Team1Score"], first_player["Team2Score"])
        self.winning_team: Literal[1, 2] = first_player["Winning_TaskForce"]
        self.bans: List[Champion] = []
        for i in range(1, 5):
            ban_id = first_player["BanId{}".format(i)]
            if not ban_id:
                continue
            ban_champ = self._api.get_champion(ban_id, language)
            if ban_champ:
                self.bans.append(ban_champ)
        self.team1: List[MatchPlayer] = []
        self.team2: List[MatchPlayer] = []
        for p in match_data:
            getattr(
                self, "team{}".format(p["TaskForce"])
            ).append(
                MatchPlayer(self._api, language, p)
            )

    @property
    def players(self) -> Generator[MatchPlayer, None, None]:
        for p in self.team1:
            yield p
        for p in self.team2:
            yield p

    def __repr__(self) -> str:
        return "{0.queue.name}({0.id}): {0.score}".format(self)


class LivePlayer(WinLoseMixin):
    """
    Represents a liva match player.

    Attributes
    ----------
    player : PartialPlayer
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
    def __init__(self, api: "PaladinsAPI", language: Language, player_data: dict):
        super().__init__(
            wins=player_data["tierWins"],
            losses=player_data["tierLosses"],
        )
        self._api = api
        from .player import PartialPlayer  # noqa, cyclic imports
        self.player = PartialPlayer(
            api, id=player_data["playerId"], name=player_data["playerName"]
        )
        self.champion: Optional[Champion] = self._api.get_champion(
            player_data["ChampionId"], language
        )
        self.rank = Rank.get(player_data["Tier"])
        self.account_level: int = player_data["Account_Level"]
        self.mastery_level: int = player_data["Mastery_Level"]

    def __repr__(self) -> str:
        player_name = self.player.name if self.player.id else "Unknown"
        champion_name = self.champion.name if self.champion is not None else "Unknown"
        return "{1}({0.player.id}): {0.account_level} level: {2}({0.mastery_level})".format(
            self, player_name, champion_name
        )


class LiveMatch:
    """
    Represents a live match.

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
    def __init__(self, api: "PaladinsAPI", language: Language, match_data: List[dict]):
        self._api = api
        first_player = match_data[0]
        self.id: int = first_player["Match"]
        self.map_name: str = first_player["mapGame"]
        self.queue = Queue.get(int(first_player["Queue"])) or Queue(0)
        self.region = Region.get(first_player["playerRegion"]) or Region(0)
        self.team1: List[LivePlayer] = []
        self.team2: List[LivePlayer] = []
        for p in match_data:
            getattr(self, "team{}".format(p["taskForce"])).append(
                LivePlayer(self._api, language, p)
            )

    def __repr__(self) -> str:
        return "{0.__class__.__name__}({0.queue.name}): {0.map_name}".format(self)

    @property
    def players(self) -> Generator[LivePlayer, None, None]:
        for p in self.team1:
            yield p
        for p in self.team2:
            yield p
