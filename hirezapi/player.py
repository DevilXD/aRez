from datetime import timedelta
from typing import Union, List, Optional

from .items import Loadout
from .exceptions import Private
from .match import PartialMatch
from .utils import convert_timestamp, PlayerStatus
from .enumerations import Language, Platform, Region
from .stats import Stats, RankedStats, ChampionStats

class PartialPlayer:
    # Nice consistency, HiRez
    def __init__(self, api, player_data: dict):
        self._api = api
        self.id = int(player_data.get("Id") or player_data.get("player_id") or player_data.get("playerId") or 0) 
        self.name = player_data.get("Name") or player_data.get("name") or player_data.get("playerName") or ''
        platform = player_data.get("Platform") or player_data.get("portal_id") or player_data.get("portalId")
        if type(platform) == str and platform.isdigit():
            platform = int(platform)
        self.platform = Platform.get(platform) #pylint: disable=no-member
    
    def __eq__(self, other) -> bool:
        assert isinstance(other, self.__class__)
        return self.id != 0 and other.id != 0 and self.id == other.id
    
    def __repr__(self):
        platform = self.platform.name if self.platform else None
        return "{0.__class__.__name__}: {0.name}({0.id} / {1})".format(self, platform)
    
    @property
    def private(self) -> bool:
        return self.id == 0

    async def expand(self) -> Optional['Player']:
        if self.private:
            raise Private
        response = await self._api.request("getplayer", [self.id])
        if response:
            return Player(self._api, response[0])

    async def get_status(self) -> Optional[PlayerStatus]:
        if self.private:
            raise Private
        response = await self._api.request("getplayerstatus", [self.id])
        if response:
            return PlayerStatus(self, response[0])
    
    async def get_friends(self) -> List['PartialPlayer']:
        if self.private:
            raise Private
        response = await self._api.request("getfriends", [self.id])
        if not response:
            return []
        return [PartialPlayer(self._api, p) for p in response]

    async def get_loadouts(self, language: Language = Language["english"]) -> List[Loadout]:
        assert isinstance(language, Language)
        if self.private:
            raise Private
        # ensure we have champion information first
        await self._api.get_champion_info(language)
        response = await self._api.request("getplayerloadouts", [self.id, language.value])
        if not response or response and response[0]["ret_msg"]:
            return []
        return [Loadout(self, language, l) for l in response]
    
    async def get_champion_stats(self, language: Language = Language["english"]) -> List[ChampionStats]:
        assert isinstance(language, Language)
        if self.private:
            raise Private
        # ensure we have champion information first
        await self._api.get_champion_info(language)
        response = await self._api.request("getgodranks", [self.id])
        if not response or response and response[0]["ret_msg"]:
            return []
        return [ChampionStats(self, language, s) for s in response]
    
    async def get_match_history(self, language: Language = Language["english"]) -> List[PartialMatch]:
        assert isinstance(language, Language)
        if self.private:
            raise Private
        # ensure we have champion information first
        await self._api.get_champion_info(language)
        response = await self._api.request("getmatchhistory", [self.id])
        if not response or response and response[0]["ret_msg"]:
            return []
        return [PartialMatch(self, language, m) for m in response]

class Player(PartialPlayer):
    def __init__(self, api, player_data):
        super().__init__(api, player_data)
        self.active_player = PartialPlayer(api, {"player_id": player_data["ActivePlayerId"]}) if player_data["ActivePlayerId"] != self.id else None
        self.merged_players = [PartialPlayer(api, p) for p in player_data["MergedPlayers"]] if player_data["MergedPlayers"] else []
        self.created_at = convert_timestamp(player_data["Created_Datetime"])
        self.last_login = convert_timestamp(player_data["Last_Login_Datetime"])
        self.level = player_data["Level"]
        self.hours_played = timedelta(hours=player_data["HoursPlayed"])
        self.champions_count = player_data["MasteryLevel"]
        self.region = Region.get(player_data["Region"]) or Region.get(0) #pylint: disable=no-member
        self.total_achievements = player_data["Total_Achievements"]
        self.total_exp = player_data["Total_Worshippers"]
        self.hz_gamer_tag = player_data["hz_gamer_tag"]
        self.hz_player_name = player_data["hz_player_name"]
        self.casual = Stats(player_data)
        self.ranked_keyboard = RankedStats(player_data["RankedKBM"])
        self.ranked_controller = RankedStats(player_data["RankedController"])
    
    