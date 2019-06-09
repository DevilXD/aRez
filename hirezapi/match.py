from datetime import datetime, timedelta
from typing import Union, List, Generator

from .mixins import KDAMixin
from .items import LoadoutCard
from .utils import convert_timestamp, Duration
from .enumerations import Queue, Language, Region

class MatchItem:
    """
    Represents an item shop's purchase.
    
    Attributes
    ----------
    item : Device
        The purchased item.
    level : int
        The level of the item purchased.
    """
    def __init__(self, item, level):
        self.item = item
        self.level = level
    
    def __repr__(self) -> str:
        return "{0.item.name}: {0.level}".format(self)

class MatchLoadout:
    """
    Represents a loadout used in a match.

    Attributes
    ----------
    cards : List[LoadoutCard]
        A list of loadout cards used.
    talent : Device
        The talent used.
    """
    def __init__(self, api, language: Language, match_data: dict):
        self.cards = []
        for i in range(1,6):
            card_id = match_data["ItemId{}".format(i)]
            if not card_id:
                continue
            self.cards.append(LoadoutCard(api.get_card(card_id, language), match_data["ItemLevel{}".format(i)]))
        self.talent = api.get_talent(match_data["ItemId6"], language)

    def __repr__(self) -> str:
        return "{}: {}/{}/{}/{}/{}".format(self.talent.name, *(c.points for c in self.cards))

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
    champion : Champion
        The champion used by the player in this match.
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
    damage_dealt : int
        The amount of damage dealt.
    damage_taken : int
        The amount of damage taken.
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
        The match's ending score. The first value is always the allied-team score, while the second one - enemy team score.
    win_status : bool
        True if the player won this match, False otherwise.
    """
    def __init__(self, player: Union['PartialPlayer', 'Player'], language: Language, match_data: dict):
        super().__init__(match_data)
        self._api = player._api
        self.player = player
        self.language = language
        self.id = match_data["Match"]
        self.champion = self._api.get_champion(match_data["ChampionId"])
        self.queue = Queue.get(match_data["Match_Queue_Id"])
        self.region = Region.get(match_data["Region"])
        self.duration = Duration(seconds=match_data["Time_In_Match_Seconds"])
        self.timestamp = convert_timestamp(match_data["Match_Time"])
        self.map_name = match_data["Map_Game"]

        self.credits      = match_data["Gold"]
        self.damage_dealt = match_data["Damage"]
        self.damage_taken = match_data["Damage_Taken"]
        self.damage_bot   = match_data["Damage_Bot"]
        self.healing_done = match_data["Healing"]
        self.healing_self = match_data["Healing_Player_Self"]
        self.healing_bot  = match_data["Healing_Bot"]

        self.objective_time = match_data["Objective_Assists"]
        self.multikill_max  = match_data["Multi_kill_Max"]
        
        my_team         = match_data["TaskForce"]
        my_score        = match_data["Team{}Score".format(my_team)]
        other_team      = 1 if my_team == 2 else 2
        other_score     = match_data["Team{}Score".format(other_team)]
        self.score      = (my_score, other_score)
        self.win_status = my_team == match_data["Winning_TaskForce"]

        self.items = []
        for i in range(1,5):
            item_id = match_data["ActiveId{}".format(i)]
            if not item_id:
                continue
            item = self._api.get_item(item_id, language)
            if item:
                level = match_data["ActiveLevel{}".format(i)] // 4 + 1
                self.items.append(MatchItem(item, level))
        self.loadout = MatchLoadout(self._api, language, match_data)
    
    def __repr__(self) -> str:
        return "{0.queue.name}: {0.champion.name}: {0.kda_text}".format(self)

    @property
    def disconnected(self) -> bool:
        """
        Checks if the player has disconnected during the match.
        This is done by checking if either `damage_bot` or `healing_bot` are non zero.
        
        Returns
        -------
        bool
            True if the player got disconnected, False otherwise.
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
        response = await self._api.request("getmatchdetails", [self.id])
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
    champion : Champion
        The champion used by the player in this match.
    loadout : MatchLoadout
        The loadout used by the player in this match.
    items : List[MatchItem]
        A list of items bought by the player during this match.
    credits : int
        The amount of credits earned this match.
    damage_dealt : int
        The amount of damage dealt.
    damage_taken : int
        The amount of damage taken.
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
    """
    def __init__(self, api, language: Language, player_data: dict):
        player_data.update({"Kills": player_data["Kills_Player"]}) #kills correction for KDAMixin
        super().__init__(player_data)
        self._api = api
        from .player import PartialPlayer # cyclic imports
        player_payload = {
            "name": player_data["playerName"],
            "player_id": int(player_data["playerId"]),
            "portal_id": int(player_data["playerPortalId"]) if player_data["playerPortalId"] else None
        }
        self.player = PartialPlayer(self._api, player_payload)
        self.champion = self._api.get_champion(player_data["ChampionId"])

        self.credits      = player_data["Gold_Earned"]
        self.damage_dealt = player_data["Damage_Done_Physical"]
        self.damage_taken = player_data["Damage_Taken"]
        self.damage_bot   = player_data["Damage_Bot"]
        self.healing_done = player_data["Healing"]
        self.healing_self = player_data["Healing_Player_Self"]
        self.healing_bot  = player_data["Healing_Bot"]

        self.objective_time = player_data["Objective_Assists"]
        self.multikill_max  = player_data["Multi_kill_Max"]

        self.kills_bot    = player_data["Kills_Bot"]
        self.double_kills = player_data["Kills_Double"]
        self.triple_kills = player_data["Kills_Triple"]
        self.quadra_kills = player_data["Kills_Quadra"]
        self.penta_kills  = player_data["Kills_Penta"]

        self.items = []
        for i in range(1,5):
            item_id = player_data["ActiveId{}".format(i)]
            if not item_id:
                continue
            item = self._api.get_item(item_id, language)
            if item:
                level = player_data["ActiveLevel{}".format(i)] + 1
                self.items.append(MatchItem(item, level))
        self.loadout = MatchLoadout(self._api, language, player_data)
    
    @property
    def disconnected(self) -> bool:
        """
        Checks if the player has disconnected during the match.
        This is done by checking if either `damage_bot` or `healing_bot` are non zero.
        
        Returns
        -------
        bool
            True if the player got disconnected, False otherwise.
        """
        return self.damage_bot > 0 or self.healing_bot > 0

    def __repr__(self) -> str:
        if self.player.id != 0:
            return "{0.player.name}({0.player.id}): ({0.kda_text}, {0.damage_dealt}, {0.healing_done})".format(self)
        else:
            return "Unknown(0): ({0.kda_text}, {0.damage_dealt}, {0.healing_done})".format(self)

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
        A list of champions banned this match.
        This is an empty list for non-ranked matches.
    map_name : str
        The name of the map played.
    score : Tuple[int, int]
        The match's ending score. The first value is the `team_1` score, while the second value - `team_2` score.
    winning_team : int
        The winning team of this match.
        This can be either `1` or `2`.
    team_1 : List[MatchPlayer]
        A list of players in the first team.
    team_2 : List[MatchPlayer]
        A list of players in the second team.
    players : Generator[MatchPlayer]
        A generator that iterates over all match players in the match.
    """
    def __init__(self, api, language: Language, match_data: List[dict]):
        self._api = api
        self.language = language
        first_player = match_data[0]
        self.id = first_player["Match"]
        self.region = Region.get(first_player["Region"])
        self.queue = Queue.get(first_player["match_queue_id"])
        self.map_name = first_player["Map_Game"]
        self.duration = Duration(seconds=first_player["Time_In_Match_Seconds"])
        self.score = (first_player["Team1Score"], first_player["Team2Score"])
        self.winning_team = first_player["Winning_TaskForce"]
        self.bans = []
        for i in range(1,5):
            ban_id = first_player["BanId{}".format(i)]
            if not ban_id:
                continue
            ban_champ = self._api.get_champion(ban_id, language)
            if ban_champ:
                self.bans.append(ban_champ)
        self.team_1 = []
        self.team_2 = []
        for p in match_data:
            getattr(self, "team_{}".format(p["TaskForce"])).append(MatchPlayer(self._api, language, p))
    
    @property
    def players(self) -> Generator[MatchPlayer, None, None]:
        for p in self.team_1:
            yield p
        for p in self.team_2:
            yield p

    def __repr__(self) -> str:
        return "{0.queue.name}({0.id}): {0.score}".format(self)
