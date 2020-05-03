from __future__ import annotations

import re
import asyncio
import logging
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta, timezone
from typing import (
    Any, Optional, Union, List, Dict, Iterable, Sequence, AsyncGenerator, Literal, overload
)

from .match import Match
from .utils import chunk
from .status import ServerStatus
from .cache import DataCache, CacheEntry
from .exceptions import Private, NotFound
from .player import Player, PartialPlayer
from .enumerations import Language, Platform, Queue, PC_PLATFORMS


__all__ = ["PaladinsAPI"]
logger = logging.getLogger(__package__)


class PaladinsAPI(DataCache):
    """
    The main Paladins API.

    Inherits from `DataCache`.

    .. note::

        You can request your developer ID and authorization key `here.
        <https://fs12.formsite.com/HiRez/form48/secure_index.html>`_

    Parameters
    ----------
    dev_id : Union[int, str]
        Your developer's ID (devId).
    auth_key : str
        Your developer's authentication key (authKey).
    loop : Optional[asyncio.AbstractEventLoop]
        The event loop you want to use for this API.\n
        Default loop is used when not provided.
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
        super().__init__("http://api.paladins.com/paladinsapi.svc", dev_id, auth_key, loop=loop)
        self._server_status: Optional[ServerStatus] = None

    async def __aenter__(self) -> PaladinsAPI:
        return self

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
        # Use a lock to ensure we're not fetching this twice in quick succession
        async with self._locks["server_status"]:
            if (
                self._server_status is None
                or datetime.utcnow() - timedelta(minutes=1) >= self._server_status.timestamp
                or force_refresh
            ):
                logger.info(f"api.get_server_status({force_refresh=}) -> fetching new")
                response = await self.request("gethirezserverstatus")
                if response:
                    self._server_status = ServerStatus(response)
            else:
                logger.info(f"api.get_server_status({force_refresh=}) -> using cached")

        return self._server_status

    async def get_champion_info(
        self, language: Optional[Language] = None, force_refresh: bool = False
    ) -> Optional[CacheEntry]:
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
        Optional[CacheEntry]
            An object containing all champions, cards, talents and items information
            in the chosen language.\n
            `None` is returned if there was no cached information and fetching returned
            an empty response.
        """
        assert language is None or isinstance(language, Language)
        if language is None:
            language = self._default_language
        logger.info(f"api.get_champion_info({language=}, {force_refresh=})")
        return await self._fetch_entry(language, force_refresh=force_refresh)

    def wrap_player(
        self,
        player_id: int,
        player_name: str = '',
        platform: Union[str, int] = 0,
        private: bool = False,
    ) -> PartialPlayer:
        """
        Wraps player ID, Name and Platform into a `PartialPlayer` object.

        Note that since there is no input validation, there's no guarantee an object created
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
        logger.debug(f"api.wrap_player({player_id=}, {player_name=}, {platform=}, {private=})")
        return PartialPlayer(
            self, id=player_id, name=player_name, platform=platform, private=private
        )

    @overload
    async def get_player(
        self, player: Union[int, str], *, return_private: Literal[False] = False
    ) -> Player:
        ...

    @overload
    async def get_player(
        self, player: Union[int, str], *, return_private: Literal[True]
    ) -> Union[Player, PartialPlayer]:
        ...

    async def get_player(
        self, player: Union[int, str], *, return_private: bool = False
    ) -> Union[Player, PartialPlayer]:
        """
        Fetches a Player object for the given player ID or player name.

        Only players with `Platform.PC`, `Platform.Steam` and `Platform.Discord`
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
        Union[Player, PartialPlayer]
            An object containing stats information about the player requested.\n
            `PartialPlayer` objects are only returned for private profiles and appropriate
            arguments used.

        Raises
        ------
        NotFound
            The player's profile doesn't exist / couldn't be found.
        Private
            The player's profile was private.
        """
        assert isinstance(player, (int, str))
        player = str(player)  # explicit cast to str
        # save on the request by raising Notfound for zero straight away
        if player == '0':
            raise NotFound("Player")
        logger.info(f"api.get_player({player=}, {return_private=})")
        player_list = await self.request("getplayer", player)
        if not player_list:
            # No one got returned
            raise NotFound("Player")
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
        self, player_ids: Iterable[int], *, return_private: Literal[False] = False
    ) -> Sequence[Player]:
        ...

    @overload
    async def get_players(
        self, player_ids: Iterable[int], *, return_private: Literal[True]
    ) -> Sequence[Union[Player, PartialPlayer]]:
        ...

    async def get_players(
        self, player_ids: Iterable[int], *, return_private: bool = False
    ) -> Sequence[Union[Player, PartialPlayer]]:
        """
        Fetches multiple players in a batch, and returns their list. Removes duplicates.

        Uses up a single request for every multiple of 20 unique player IDs passed.

        Parameters
        ----------
        player_ids : Iterable[int]
            An iterable of player IDs you want to fetch.
        return_private : bool
            When set to `True` and one of the requested profiles is determined private,
            this method will return a `PartialPlayer` object with the player ID and privacy flag
            set.\n
            When set to `False`, private profiles are omitted from the output list.\n
            Defaults to `False`.

        Returns
        -------
        List[Union[Player, PartialPlayer]]
            A list of players requested.\n
            `PartialPlayer` objects are only returned for private profiles and appropriate
            arguments used.
            Some players might not be included in the output if they weren't found,
            or their profile was private.
        """
        ids_list: List[int] = list(OrderedDict.fromkeys(player_ids))  # remove duplicates
        assert all(isinstance(player_id, int) for player_id in ids_list)
        if 0 in ids_list:
            # remove private accounts
            ids_list.remove(0)
        if not ids_list:
            return []
        logger.info(
            f"api.get_players(player_ids=[{', '.join(map(str, ids_list))}], {return_private=})"
        )
        player_list: List[Union[Player, PartialPlayer]] = []
        for chunk_ids in chunk(ids_list, 20):
            chunk_response = await self.request("getplayerbatch", ','.join(map(str, chunk_ids)))
            chunk_players: List[Union[Player, PartialPlayer]] = []
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
        self, player_name: str, platform: Optional[Platform] = None, *, return_private: bool = True
    ) -> List[PartialPlayer]:
        """
        Fetches all players whose name matches the name specified.
        The search is fuzzy - player name capitalisation doesn't matter.

        Uses up a single request.

        .. note::

            Searching on all platforms may limit the number of players returned to ~500.
            Specifying a particular platform does not have this limitation.

        Parameters
        ----------
        player_name : str
            Player name you want to search for.
        platform : Optional[Platform]
            Platform you want to limit the search to.\n
            Specifying `None` will search on all platforms.\n
            Defaults to `None`.
        return_private : bool
            When set to `True` and one of the requested profiles is determined private,
            this method will return a `PartialPlayer` object with the player ID and privacy flag
            set.\n
            When set to `False`, private profiles are omitted from the output list.\n
            Defaults to `True`.

        Returns
        -------
        List[PartialPlayer]
            A list of players whose name (and optionally platform) matches
            the specified name.\n
            Note that some of them might be set as private, unless appropriate input parameters
            were used.

        Raises
        ------
        NotFound
            There was no player for the given name (and optional platform) found.
        """
        assert isinstance(player_name, str)
        assert platform is None or isinstance(platform, Platform)
        list_response: List[Dict[str, Any]]
        if platform is not None:
            # Specific platform
            logger.info(
                f"api.search_players({player_name=}, platform={platform.name}, {return_private=})"
            )
            if platform in PC_PLATFORMS:
                # PC platforms, with unique names
                list_response = await self.request("getplayeridbyname", player_name)
            else:
                # Console platforms, names might be duplicated
                list_response = await self.request(
                    "getplayeridsbygamertag", platform.value, player_name
                )
        else:
            # All platforms
            logger.info(f"api.search_players({player_name=}, {platform=}, {return_private=})")
            response = await self.request("searchplayers", player_name)
            player_name = player_name.lower()
            list_response = [r for r in response if r["Name"].lower() == player_name]
        if not list_response:
            raise NotFound("Player")
        if return_private:
            # Include private accounts
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
        else:
            # Omit private accounts
            return [
                PartialPlayer(
                    self,
                    id=p["player_id"],
                    name=p["Name"],
                    platform=p["portal_id"],
                )
                for p in list_response
                if p["privacy_flag"] != 'y'
            ]

    async def get_from_platform(
        self, platform_id: int, platform: Platform
    ) -> PartialPlayer:
        """
        Fetches a PartialPlayer linked with the platform ID specified.

        .. note::

            This method doesn't set the `PartialPlayer.name` attribute, meaning that it will
            remain as an empty string. This is a limitation of the Hi-Rez API, not the library.

        Uses up a single request.

        Parameters
        ----------
        platform_id : int
            The platform-specific ID of the linked player.\n
            This is usually a Hi-Rez account ID, SteamID64, Discord User ID, etc.
        platform : Platform
            The platform this ID is for.

        Returns
        -------
        PartialPlayer
            The player this platform ID is linked to.

        Raises
        ------
        NotFound
            The linked profile doesn't exist / couldn't be found.
        """
        assert isinstance(platform_id, int)
        assert isinstance(platform, Platform)
        logger.info(f"api.get_from_platform({platform_id=}, platform={platform.name})")
        response = await self.request("getplayeridbyportaluserid", platform.value, platform_id)
        if not response:
            raise NotFound("Linked profile")
        p = response[0]
        return PartialPlayer(
            self, id=p["player_id"], platform=p["portal_id"], private=p["privacy_flag"] == 'y'
        )

    async def get_match(
        self, match_id: int, language: Optional[Language] = None, *, expand_players: bool = False
    ) -> Match:
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
        expand_players : bool
            When set to `True`, partial player objects in the returned match object will
            automatically be expanded into full `Player` objects, if possible.\n
            Uses an addtional request to do the expansion.\n
            Defaults to `False`.

        Returns
        -------
        Match
            A match for the ID specified.

        Raises
        ------
        NotFound
            The match wasn't available on the server.
        """
        assert isinstance(match_id, int)
        assert language is None or isinstance(language, Language)
        if language is None:
            language = self._default_language
        # ensure we have champion information first
        await self._ensure_entry(language)
        logger.info(f"api.get_match({match_id=}, {language=}, {expand_players=})")
        response = await self.request("getmatchdetails", match_id)
        if not response:
            raise NotFound("Match")
        players: Dict[int, Player] = {}
        if expand_players:
            players_list = await self.get_players((int(p["playerId"]) for p in response))
            players = {p.id: p for p in players_list}
        return Match(self, language, response, players)

    async def get_matches(
        self,
        match_ids: Iterable[int],
        language: Optional[Language] = None,
        *,
        expand_players: bool = False,
    ) -> List[Match]:
        """
        Fetches multiple matches in a batch, for the given Match IDs. Removes duplicates.

        Uses up a single request for every multiple of 10 unique match IDs passed.

        Parameters
        ----------
        match_ids : Iterable[int]
            An iterable of Match IDs you want to fetch.
        language : Optional[Language]
            The `Language` you want to fetch the information in.\n
            Default language is used if not provided.
        expand_players : bool
            When set to `True`, partial player objects in the returned match objects will
            automatically be expanded into full `Player` objects, if possible.\n
            Uses an addtional request for every 20 unique players to do the expansion.\n
            Defaults to `False`.

        Returns
        -------
        List[Match]
            A list of the available matches requested.\n
            Some of the matches can be not present if they weren't available on the server.
        """
        assert language is None or isinstance(language, Language)
        ids_list: List[int] = list(OrderedDict.fromkeys(match_ids))  # remove duplicates
        if not ids_list:
            return []
        assert all(isinstance(match_id, int) for match_id in ids_list)
        if language is None:
            language = self._default_language
        # ensure we have champion information first
        await self._ensure_entry(language)
        logger.info(
            f"api.get_matches(match_ids=[{', '.join(map(str, ids_list))}], "
            f"{language=}, {expand_players=})"
        )
        matches: List[Match] = []
        players: Dict[int, Player] = {}
        for chunk_ids in chunk(ids_list, 10):  # chunk the IDs into groups of 10
            response = await self.request("getmatchdetailsbatch", ','.join(map(str, chunk_ids)))
            bunched_matches: Dict[int, list] = defaultdict(list)
            for p in response:
                bunched_matches[p["Match"]].append(p)
            if expand_players:
                players_list = await self.get_players(
                    (int(p["playerId"]) for p in response if int(p["playerId"]) not in players)
                )
                players.update({p.id: p for p in players_list})
            chunked_matches: List[Match] = [
                Match(self, language, match_list, players)
                for match_list in bunched_matches.values()
            ]
            matches.extend(chunked_matches)
        return matches

    async def get_matches_for_queue(
        self,
        queue: Queue,
        language: Optional[Language] = None,
        *,
        start: datetime,
        end: datetime,
        reverse: bool = False,
        local_time: bool = False,
        expand_players: bool = False,
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
        local_time : bool
            When set to `True`, the timestamps provided are assumed to represent the local system
            time (in your local timezone), and will be converted to UTC before processing.\n
            When set to `False`, the timestamps provided are assumed to already represent UTC and
            no conversion will occur.\n
            Defaults to `False`.
        expand_players : bool
            When set to `True`, partial player objects in the returned match object will
            automatically be expanded into full `Player` objects, if possible.\n
            Uses an addtional request for every 20 unique players to do the expansion.\n
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
        assert isinstance(expand_players, bool)
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
        if local_time:
            # assume local timezone, convert objects into UTC ones, matching server time
            start = start.astimezone(timezone.utc)
            end = end.astimezone(timezone.utc)
        if language is None:
            language = self._default_language
        # ensure we have champion information first
        await self._ensure_entry(language)
        logger.info(
            f"api.get_matches_for_queue({queue=}, {language=}, {start=} UTC, {end=} UTC, "
            f"{reverse=}, {local_time=}, {expand_players=})"
        )

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
                        yield (end.strftime("%Y%m%d"), f"{end.hour},{end.minute:02}")
                # round up to the nearest hour
                closest_hour = start.replace(minute=0) + timedelta(hours=1)
                while end > closest_hour and end > start:
                    end -= one_hour
                    yield (end.strftime("%Y%m%d"), str(end.hour))
                if start.minute > 0:
                    while end > start:
                        end -= ten_minutes
                        yield (end.strftime("%Y%m%d"), f"{end.hour},{end.minute:02}")
            else:
                if start.minute > 0:
                    # round up to the nearest hour
                    closest_hour = start.replace(minute=0) + timedelta(hours=1)
                    while start < closest_hour and start < end:
                        yield (
                            start.strftime("%Y%m%d"), f"{start.hour},{start.minute:02}"
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
                            start.strftime("%Y%m%d"), f"{start.hour},{start.minute:02}"
                        )
                        start += ten_minutes

        # Use the generated date and hour values to iterate over and fetch matches
        players: Dict[int, Player] = {}
        for date, hour in date_gen(start, end, reverse=reverse):
            response = await self.request("getmatchidsbyqueue", queue.value, date, hour)
            if reverse:
                match_ids = [
                    int(e["Match"])
                    for e in reversed(response)
                    if e["Active_Flag"] == 'n'
                ]
            else:
                match_ids = [int(e["Match"]) for e in response if e["Active_Flag"] == 'n']
            for chunk_ids in chunk(match_ids, 10):  # chunk the IDs into groups of 10
                response = await self.request(
                    "getmatchdetailsbatch", ','.join(map(str, chunk_ids))
                )
                bunched_matches: Dict[int, list] = defaultdict(list)
                for p in response:
                    bunched_matches[p["Match"]].append(p)
                if expand_players:
                    players_list = await self.get_players(
                        (int(p["playerId"]) for p in response if int(p["playerId"]) not in players)
                    )
                    players.update({p.id: p for p in players_list})
                chunked_matches = [
                    Match(self, language, match_list, players)
                    for match_list in bunched_matches.values()
                ]
                chunked_matches.sort(key=lambda m: chunk_ids.index(m.id))
                for match in chunked_matches:
                    yield match
