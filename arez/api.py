import re
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, List, Dict, AsyncGenerator, Literal, overload

from .match import Match
from .utils import chunk
from .endpoint import Endpoint
from .exceptions import Private
from .status import ServerStatus
from .player import Player, PartialPlayer
from .cache import DataCache, ChampionInfo
from .enumerations import Language, Platform, Queue


class PaladinsAPI:
    """
    The main Paladins API.

    Parameters
    ----------
    dev_id : Union[int, str]
        Your developer's ID (devId).
    auth_key : str
        Your developer's authentication key (authKey).
    loop : Optional[asyncio.AbstractEventLoop]
        The event loop you want to use for this API.\n
        Default loop is used when not provided.

    Attributes
    ----------
    cache : DataCache
        The internal data cache, that stores all intermediate information about champions, cards,
        talents, abilities, shop items, etc.
    """
    def __init__(
        self,
        dev_id: Union[int, str],
        auth_key: str,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        if loop is None:
            loop = asyncio.get_event_loop()
        # don't store the endpoint - the API should have no access to it's instance other than
        # the request and close methods
        endpoint = Endpoint("http://api.paladins.com/paladinsapi.svc", dev_id, auth_key, loop=loop)
        # forward endpoint request and close methods
        self.request = endpoint.request
        self.close = endpoint.close
        # cache stuff
        self._server_status: Optional[ServerStatus] = None
        self.cache = DataCache(self)
        # forward cache get methods
        self.get_champion = self.cache.get_champion
        self.get_card     = self.cache.get_card
        self.get_talent   = self.cache.get_talent
        self.get_item     = self.cache.get_item
        # default language
        self._default_language = Language.English

    # async with integration
    async def __aenter__(self) -> "PaladinsAPI":
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        await self.close()

    def set_default_language(self, language: Language):
        """
        Sets the default language used by the API in places where one is not provided
        by the user.\n
        The default language set is `Language.English`.

        Parameters
        ----------
        language : Language
            The new default language you want to set.
        """
        assert isinstance(language, Language)
        self._default_language = language

    async def get_server_status(self, force_refresh: bool = False) -> Optional[ServerStatus]:
        """
        Fetches the server status.

        To preserve requests, the status returned is cached once every minute.
        Use the ``force_refresh`` parameter to override this behavior.

        Uses up one request each time the cache is refreshed.

        Parameters
        ----------
        force_refresh : bool
            Bypasses the cache, forcing a fetch and returning a new object.\n
            Defaults to `False`.

        Returns
        -------
        Optional[ServerStatus]
            The server status object.\n
            `None` is returned if there is no cached status and fetching returned
            an empty response.
        """
        if (
            self._server_status is None
            or datetime.utcnow() - timedelta(minutes=1) >= self._server_status.timestamp
            or force_refresh
        ):
            response = await self.request("gethirezserverstatus")
            if response:
                self._server_status = ServerStatus(response)

        return self._server_status

    async def get_champion_info(
        self, language: Optional[Language] = None, force_refresh: bool = False
    ) -> Optional[ChampionInfo]:
        """
        Fetches the champion information.

        To preserve requests, the information returned is cached once every 12 hours.
        Use the ``force_refresh`` parameter to override this behavior.

        Uses up two requests each time the cache is refreshed, per language.

        Parameters
        ----------
        language : Optional[Language]
            The `Language` you want to fetch the information in.\n
            Default language is used if not provided.
        force_refresh : bool
            Bypasses the cache, forcing a fetch and returning a new object.\n
            Defaults to `False`.

        Returns
        -------
        Optional[ChampionInfo]
            An object containing all champions, cards, talents and items information
            in the chosen language.\n
            `None` is returned if there was no cached information and fetching returned
            an empty response.
        """
        assert language is None or isinstance(language, Language)
        if language is None:
            language = self._default_language
        entry = await self.cache._fetch_entry(language, force_refresh=force_refresh)
        return entry

    def wrap_player(
        self,
        player_id: int,
        player_name: str = '',
        platform: Union[str, int] = 0,
        private: bool = False,
    ) -> PartialPlayer:
        """
        Wraps player ID, Name and Platform into a `PartialPlayer` object.

        Note that since there is no input validation, so there's no guarantee an object created
        this way will return any meaningful results when it's methods are used.

        Parameters
        ----------
        player_id : int
            The player ID you want to get the object for.
        player_name : str
            The player Name you want the object to have.\n
            Defaults to an empty string.
        platform : Union[str, int]
            The platform you want the object to have.\n
            Defaults to `Platform.Unknown`.
        private : bool
            A boolean flag indicating if this profile should be considered private or not.\n
            Defaults to `False`.

        Returns
        -------
        PartialPlayer
            The wrapped player object.
        """
        assert isinstance(player_id, int)
        return PartialPlayer(
            self, id=player_id, name=player_name, platform=platform, private=private
        )

    @overload
    async def get_player(
        self, player: Union[int, str], *, return_private: Literal[False] = False
    ) -> Optional[Player]:
        ...

    @overload
    async def get_player(
        self, player: Union[int, str], *, return_private: Literal[True]
    ) -> Optional[Union[Player, PartialPlayer]]:
        ...

    async def get_player(self, player: Union[int, str], *, return_private: bool = False):
        """
        Fetches a Player object for the given player ID or player name.

        Only players with `Platform.Steam`, `Platform.HiRez` and `Platform.Discord`
        platforms (PC players) will be returned when using this method with player name
        as input. For player ID inputs, players from all platforms will be returned.

        Uses up a single request.

        Parameters
        ----------
        player : Union[int, str]
            Player ID or player name of the player you want to get object for.
        return_private : bool
            When set to `True` and the requested profile is determined private, this method will
            return a `PartialPlayer` object with the player ID and privacy flag set.\n
            When set to `False`, the `Private` exception will be raised instead.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Union[Player, PartialPlayer]]
            An object containing stats information about the player requested.\n
            `PartialPlayer` objects are only returned for private profiles and appropriate
            arguments used.\n
            `None` is returned if a Player for the given ID or Name could not be found.

        Raises
        ------
        Private
            The player's profile was private.
        """
        assert isinstance(player, (int, str))
        player = str(player)  # explicit cast to str
        # save on the request by returning None for zero straight away
        if player == '0':
            return None
        player_list = await self.request("getplayer", player)
        if not player_list:
            # No one got returned
            return None
        player_data = player_list[0]
        # Check to see if their profile is private by chance
        ret_msg = player_data["ret_msg"]
        if ret_msg:
            # 'Player Privacy Flag set for:
            # playerIdStr=<arg>; playerIdType=1; playerId=479353'
            if return_private:
                match = re.search(r'playerIdType=([0-9]{1,2}); playerId=([0-9]+)', ret_msg)
                if match:  # TODO: use the walrus operator here
                    return PartialPlayer(
                        self, id=match.group(2), platform=match.group(1), private=True
                    )
            raise Private
        return Player(self, player_data)

    @overload
    async def get_players(
        self, player_ids: List[int], *, return_private: Literal[False] = False
    ) -> List[Player]:
        ...

    @overload
    async def get_players(
        self, player_ids: List[int], *, return_private: Literal[True]
    ) -> List[Union[Player, PartialPlayer]]:
        ...

    async def get_players(self, player_ids: List[int], *, return_private: bool = False):
        """
        Fetches multiple players in a batch.

        Uses up a single request for every multiple of 20 player IDs passed.

        Parameters
        ----------
        player_ids : List[int]
            The list of player IDs you want to fetch.
        return_private : bool
            When set to `True` and one of the requested profile is determined private,
            this method will return a `PartialPlayer` object with the player ID and privacy flag
            set.\n
            When set to `False`, private profiles are ommited from the output list.\n
            Defaults to `False`.

        Returns
        -------
        List[Union[Player, PartialPlayer]]
            A list of players requested.\n
            Some players might not be included in the output if they weren't found,
            or their profile was private.
        """
        assert isinstance(player_ids, list)
        assert all(isinstance(pid, int) for pid in player_ids)
        if not player_ids:
            return []
        player_list: List[Union[Player, PartialPlayer]] = []
        for chunk_ids in chunk(player_ids, 20):
            chunk_response = await self.request("getplayerbatch", ','.join(map(str, chunk_ids)))
            chunk_players: list = []
            for p in chunk_response:
                ret_msg = p["ret_msg"]
                if not ret_msg:
                    # We're good, just pack it up
                    chunk_players.append(Player(self, p))
                elif return_private:
                    # Pack up a private player object
                    match = re.search(r'playerId=([0-9]+)', ret_msg)
                    if match:  # TODO: use the walrus operator here
                        chunk_players.append(PartialPlayer(self, id=match.group(1), private=True))

            chunk_players.sort(key=lambda p: chunk_ids.index(p.id))
            player_list.extend(chunk_players)
        return player_list

    async def search_players(
        self, player_name: str, platform: Optional[Platform] = None
    ) -> List[PartialPlayer]:
        """
        Fetches all players whose name matches the name specified.

        The search is fuzzy - player name capitalisation doesn't matter.

        Uses up a single request.

        Parameters
        ----------
        player_name : str
            Player name you want to search for.
        platform : Optional[Platform]
            Platform you want to limit the search to.\n
            Specifying `None` will search on all platforms.\n
            Defaults to `None`.

        Returns
        -------
        List[PartialPlayer]
            A list of partial players whose name matches the specified name.\n
            Note that some of them might be set as private.
        """
        assert isinstance(player_name, str)
        assert isinstance(platform, (None.__class__, Platform))
        if platform:
            if platform <= 5 or platform == 25:  # hirez, pc, steam and discord only
                list_response = await self.request("getplayeridbyname", player_name)
            else:
                list_response = await self.request(
                    "getplayeridsbygamertag", platform.value, player_name
                )
            return [
                PartialPlayer(
                    self,
                    id=p["player_id"],
                    name=player_name,
                    platform=p["portal_id"],
                    private=p["privacy_flag"] == 'y',
                )
                for p in list_response
            ]
        else:
            response = await self.request("searchplayers", player_name)
            player_name = player_name.lower()
            list_response = [r for r in response if r["Name"].lower() == player_name]
            return [
                PartialPlayer(
                    self,
                    id=p["player_id"],
                    name=p["Name"],
                    platform=p["portal_id"],
                    private=p["privacy_flag"] == 'y',
                )
                for p in list_response
            ]

    async def get_from_platform(
        self, platform_id: int, platform: Platform
    ) -> Optional[PartialPlayer]:
        """
        Fetches a PartialPlayer linked with the platform ID specified.

        Uses up a single request.

        Parameters
        ----------
        platform_id : int
            The platform-specific ID of the linked player.\n
            This is usually SteamID64, Discord User ID, etc.
        platform : Platform
            The platform this ID is for.

        Returns
        -------
        Optional[PartialPlayer]
            The player this platform ID is linked to.\n
            `None` is returned if the player couldn't be found.
        """
        assert isinstance(platform_id, int)
        assert isinstance(platform, Platform)
        response = await self.request("getplayeridbyportaluserid", platform.value, platform_id)
        if response:
            p = response[0]
            return PartialPlayer(
                self, id=p["player_id"], platform=p["portal_id"], private=p["privacy_flag"] == 'y'
            )
        return None

    async def get_match(
        self, match_id: int, language: Optional[Language] = None
    ) -> Optional[Match]:
        """
        Fetches a match for the given Match ID.

        Uses up a single request.

        Parameters
        ----------
        match_id : int
            Match ID you want to get a match for.
        language : Optional[Language]
            The `Language` you want to fetch the information in.\n
            Default language is used if not provided.

        Returns
        -------
        Optional[Match]
            A match for the ID specified.\n
            `None` is returned if the match wasn't available on the server.
        """
        assert isinstance(match_id, int)
        assert language is None or isinstance(language, Language)
        if language is None:
            language = self._default_language
        # ensure we have champion information first
        await self.get_champion_info(language)
        response = await self.request("getmatchdetails", match_id)
        if response:
            return Match(self, language, response)
        return None

    async def get_matches(
        self, match_ids: List[int], language: Optional[Language] = None
    ) -> List[Match]:
        """
        Fetches multiple matches in a batch, for the given Match IDs.

        Uses up a single request for every multiple of 10 match IDs passed.

        Parameters
        ----------
        match_ids : List[int]
            The list of Match IDs you want to fetch.
        language : Optional[Language]
            The `Language` you want to fetch the information in.\n
            Default language is used if not provided.

        Returns
        -------
        List[Match]
            A list of the available matches requested.\n
            Some of the matches can be not present if they weren't available on the server.
        """
        assert isinstance(match_ids, list)
        assert all(isinstance(mid, int) for mid in match_ids)
        assert language is None or isinstance(language, Language)
        if not match_ids:
            return []
        if language is None:
            language = self._default_language
        # ensure we have champion information first
        await self.get_champion_info(language)
        matches: List[Match] = []
        for chunk_ids in chunk(match_ids, 10):  # chunk the IDs into groups of 10
            response = await self.request("getmatchdetailsbatch", ','.join(map(str, chunk_ids)))
            bunched_matches: Dict[int, list] = {}
            for p in response:
                bunched_matches.setdefault(p["Match"], []).append(p)
            chunked_matches = [
                Match(self, language, match_list) for match_list in bunched_matches.values()
            ]
            chunked_matches.sort(key=lambda m: chunk_ids.index(m.id))
            matches.extend(chunked_matches)
        return matches

    async def get_matches_for_queue(
        self,
        queue: Queue,
        language: Optional[Language] = None,
        *,
        start: datetime,
        end: datetime,
        reverse: bool = False
    ) -> AsyncGenerator[Match, None]:
        """
        Creates an async generator that lets you iterate over all matches played
        in a particular queue, between the timestamps provided.

        Uses up a single request for every:\n
        • multiple of 10 matches returned\n
        • 10 minutes worth of matches fetched

        Whole hour time slices are optimized to use a single request instead of
        6 individual, 10 minute ones.

        Parameters
        ----------
        queue : Queue
            The `Queue` you want to fetch the matches for.
        language : Optional[Language]
            The `Language` you want to fetch the information in.\n
            Default language is used if not provided.
        start : datetime.datetime
            A UTC timestamp indicating the starting point of a time slice you want to
            fetch the matches in.
        end : datetime.datetime
            A UTC timestamp indicating the ending point of a time slice you want to
            fetch the matches in.
        reverse : bool
            Reverses the order of the matches being returned.\n
            Defaults to `False`.

        Returns
        -------
        AsyncGenerator[Match, None]
            An async generator yielding matches played in the queue specified, between the
            timestamps specified.
        """
        assert isinstance(queue, Queue)
        assert language is None or isinstance(language, Language)
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert isinstance(reverse, bool)
        # normalize and floor start and end to 10 minutes step resolution
        start = start.replace(minute=(
            start.minute // 10 * 10
        ), second=0, microsecond=0)
        end = end.replace(minute=(
            end.minute // 10 * 10
        ), second=0, microsecond=0)
        if start >= end:
            # the time slice is too short - save on processing by quitting early
            return
        # convert aware objects into UTC ones, matching server time
        start = start.astimezone(timezone.utc)
        end = end.astimezone(timezone.utc)
        if language is None:
            language = self._default_language
        # ensure we have champion information first
        await self.get_champion_info(language)

        # Generates API-valid series of date and hour parameters
        def date_gen(start, end, *, reverse=False):
            one_hour = timedelta(hours=1)
            ten_minutes = timedelta(minutes=10)
            if reverse:
                if end.minute > 0:
                    # round down to the nearest hour
                    closest_hour = end.replace(minute=0)
                    while end > closest_hour and end > start:
                        end -= ten_minutes
                        yield (end.strftime("%Y%m%d"), "{},{:02}".format(end.hour, end.minute))
                # round up to the nearest hour
                closest_hour = start.replace(minute=0) + timedelta(hours=1)
                while end > closest_hour and end > start:
                    end -= one_hour
                    yield (end.strftime("%Y%m%d"), str(end.hour))
                if start.minute > 0:
                    while end > start:
                        end -= ten_minutes
                        yield (end.strftime("%Y%m%d"), "{},{:02}".format(end.hour, end.minute))
            else:
                if start.minute > 0:
                    # round up to the nearest hour
                    closest_hour = start.replace(minute=0) + timedelta(hours=1)
                    while start < closest_hour and start < end:
                        yield (
                            start.strftime("%Y%m%d"), "{},{:02}".format(start.hour, start.minute)
                        )
                        start += ten_minutes
                # round down to the nearest hour
                closest_hour = end.replace(minute=0)
                while start < closest_hour and start < end:
                    yield (start.strftime("%Y%m%d"), str(start.hour))
                    start += one_hour
                if end.minute > 0:
                    while start < end:
                        yield (
                            start.strftime("%Y%m%d"), "{},{:02}".format(start.hour, start.minute)
                        )
                        start += ten_minutes

        # Use the generated date and hour values to iterate over and fetch matches
        for date, hour in date_gen(start, end, reverse=reverse):
            response = await self.request("getmatchidsbyqueue", queue.value, date, hour)
            if reverse:
                match_ids = [
                    int(e["Match"])
                    for e in reversed(response)
                    if e["Active_Flag"] == "n"
                ]
            else:
                match_ids = [int(e["Match"]) for e in response if e["Active_Flag"] == "n"]
            for chunk_ids in chunk(match_ids, 10):  # chunk the IDs into groups of 10
                response = await self.request(
                    "getmatchdetailsbatch", ','.join(map(str, chunk_ids))
                )
                bunched_matches: Dict[int, list] = {}
                for p in response:
                    bunched_matches.setdefault(p["Match"], []).append(p)
                chunked_matches = [
                    Match(self, language, match_list) for match_list in bunched_matches.values()
                ]
                chunked_matches.sort(key=lambda m: chunk_ids.index(m.id))
                for match in chunked_matches:
                    yield match
