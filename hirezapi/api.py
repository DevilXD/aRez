import asyncio
from datetime import datetime, timedelta
from typing import Union, List, Optional

from .match import Match
from .items import Device
from .endpoint import Endpoint
from .champion import Champion
from .cache import DataCache, ChampionInfo
from .player import Player, PartialPlayer
from .utils import convert_timestamp, ServerStatus
from .enumerations import Language, Platform, Queue

class PaladinsAPI:
    
    Platform = Platform
    Language = Language
    Queue = Queue
    
    def __init__(self, dev_id, api_key):
        self.endpoint = Endpoint("http://api.paladins.com/paladinsapi.svc", dev_id, api_key)
        self.server_status = None
        self.cache = DataCache()
        # forward endpoint request and close methods
        self.request = self.endpoint.request
        self.close = self.endpoint.close
        # forward cache get methods
        self.get_champion = self.cache.get_champion
        self.get_card     = self.cache.get_card
        self.get_talent   = self.cache.get_talent
        self.get_item     = self.cache.get_item
    
    # async with integration
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, traceback):
        await self.close()
    
    async def get_server_status(self, force_refresh: bool = False) -> Optional[ServerStatus]:
        now = datetime.utcnow()

        if self.server_status is None or now >= self.server_status[1] or force_refresh:
            response = await self.request("gethirezserverstatus")
            if response:
                self.server_status = (ServerStatus(response), now + timedelta(minutes=1))
        
        if self.server_status:
            return self.server_status[0]
    
    async def get_champion_info(self, language: Language = Language["english"], force_refresh: bool = False) -> Optional[ChampionInfo]:
        assert isinstance(language, Language)

        if self.cache._needs_refreshing(language) or force_refresh:
            champions_response = await self.request("getgods", [language.value])
            items_response = await self.request("getitems", [language.value])
            if champions_response and items_response:
                self.cache[language] = (champions_response, items_response)

        return self.cache[language]

    def get_player_from_id(self, player_id: int) -> PartialPlayer:
        assert isinstance(player_id, int)
        return PartialPlayer(self, {"player_id": player_id})
    
    async def get_player(self, player: Union[int, str]) -> Optional[Player]:
        assert isinstance(player, (int, str))
        player_list = await self.request("getplayer", [player])
        if player_list:
            return Player(self, player_list[0])
    
    async def search_players(self, player_name: str, platform: Platform = None) -> List[PartialPlayer]:
        assert isinstance(player_name, str)
        assert isinstance(platform, (None.__class__, Platform))
        player_name = player_name.lower()
        if platform:
            if platform.value <= 5: # hirez, pc and steam only
                list_response = await self.request("getplayeridbyname", [player_name])
            else:
                list_response = await self.request("getplayeridsbygamertag", [platform.value, player_name])
        else:
            response = await self.request("searchplayers", [player_name])
            list_response = [r for r in response if r["Name"].lower() == player_name]
        return [PartialPlayer(self, p) for p in list_response]
    
    async def get_match(self, match_id: int, language: Language = Language["english"]) -> Optional[Match]:
        assert isinstance(match_id, int)
        assert isinstance(language, Language)
        # ensure we have champion information first
        await self.get_champion_info(language)
        response = await self.request("getmatchdetails", [match_id])
        if response:
            return Match(self, language, response)
