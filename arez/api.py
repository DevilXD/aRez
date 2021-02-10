from __future__ import annotations

import re
import asyncio
import logging
from operator import itemgetter
from datetime import datetime, timedelta, timezone
from typing import (
    Any, Optional, Union, List, Dict, Tuple, Iterable, Sequence, AsyncGenerator, Literal, overload
)

from .mixins import CacheClient
from .bounty import BountyItem
from .status import ServerStatus
from .exceptions import HTTPException
from .match import Match, _get_players
from .cache import DataCache, CacheEntry
from .exceptions import Private, NotFound
from .player import Player, PartialPlayer
from .enums import Language, Platform, Queue, PC_PLATFORMS
from .utils import chunk, group_by, _date_gen, _convert_timestamp, _deduplicate


__all__ = ["PaladinsAPI"]
logger = logging.getLogger(__package__)


class PaladinsAPI(DataCache):
    """
    The main Paladins API.

    Inherits from `DataCache`.

    .. note::

        You can request your developer ID and authorization key `here.
        <https://fs12.formsite.com/HiRez/form48/secure_index.html>`_


    .. note::

        In addition to the exceptions specified below, each API request can result
        in two additional exceptions being raised:

        `Unavailable`
            The API is currently unavailable.
        `HTTPException`
            Fetching the information requested failed due to connection problems.

    Parameters
    ----------
    dev_id : Union[int, str]
        Your developer's ID (devId).
    auth_key : str
        Your developer's authentication key (authKey).
    cache : bool
        When set to `False`, this disables the data cache. This makes most objects returned
        from the API be `CacheObject` instead of their respective data-rich counterparts.
        Defaults to `True`.
    initialize : Union[bool, Language]
        When set to `True`, it launches a task that will initialize the cache with
        the default (English) language.\n
        Can be set to a `Language` instance, in which case that language will be set as default
        first, before initializing.\n
        Defaults to `False`, where no initialization occurs.
    loop : Optional[asyncio.AbstractEventLoop]
        The event loop you want to use for this API.\n
        Default loop is used when not provided.
    """
    def __init__(
        self,
        dev_id: Union[int, str],
        auth_key: str,
        *,
        cache: bool = True,
        initialize: Union[bool, Language] = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        if loop is None:  # pragma: no branch
            loop = asyncio.get_event_loop()
        self._server_status: Optional[ServerStatus] = None
        super().__init__(
            "http://api.paladins.com/paladinsapi.svc",
            dev_id,
            auth_key,
            loop=loop,
            enabled=cache,
            initialize=initialize,
        )

    # solely for typing, __aexit__ exists in the DataCache
    async def __aenter__(self) -> PaladinsAPI:
        return self

    async def get_server_status(self, *, force_refresh: bool = False) -> ServerStatus:
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
        ServerStatus
            The server status object.

        Raises
        ------
        NotFound
            There was no cached status and fetching returned an empty response.
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
                if response and not response[0]["ret_msg"]:
                    self._server_status = ServerStatus(response)
            else:
                logger.info(f"api.get_server_status({force_refresh=}) -> using cached")
        if self._server_status is None:
            raise NotFound("Server status")
        return self._server_status

    async def get_champion_info(
        self,
        language: Optional[Language] = None,
        *,
        force_refresh: bool = False,
        cache: Optional[bool] = None,
    ) -> CacheEntry:
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
        cache : Optional[bool]
            Lets you decide if the received information should be cached or not.\n
            Setting this to `True` forces the object to be cached, even
            when the cache is disabled.\n
            Setting this to `False` will never cache the object.\n
            Default behavior follows the cache existence setting.

        Returns
        -------
        CacheEntry
            An object containing all champions, cards, talents and items information
            in the chosen language.

        Raises
        ------
        NotFound
            The champion information wasn't available on the server.
        """
        assert language is None or isinstance(language, Language)
        if language is None:
            language = self._default_language
        logger.info(f"api.get_champion_info({language=}, {force_refresh=})")
        entry = await self._fetch_entry(language, force_refresh=force_refresh, cache=cache)
        if entry is None:
            raise NotFound("Champion information")
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

        .. warning::

            Note that since there is no input validation, there's no guarantee an object created
            this way will return any meaningful results when it's methods are used. This method
            is here purely for those who'd like to store player objects in something like
            a database, offering the possibility of re-wrapping the stored data back into
            a valid player object.

            This **should not** be used to fetch stats for players based on their ID - use
            `get_player` for this purpose instead.

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
                if match:  # pragma: no branch  # TODO: use the walrus operator here
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
        ids_list: List[int] = _deduplicate(player_ids, 0)  # also remove private accounts
        if not ids_list:
            return []
        assert all(isinstance(player_id, int) for player_id in ids_list)
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
                    if match:  # pragma: no branch  # TODO: use the walrus operator here
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
        # fail early for an incorrect platform type
        if platform is not None and not isinstance(platform, Platform):
            raise TypeError(
                f"platform arg has to be of type arez.Platform, not {type(platform)!r}"
            )
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
            # pre-process the names to prioritize unique names first
            for player_dict in response:
                if name := player_dict["hz_player_name"]:
                    player_dict["Name"] = name
            list_response = [r for r in response if r["Name"].lower() == player_name]
        if not return_private:
            # Exclude private accounts
            list_response = [p for p in list_response if p["privacy_flag"] != 'y']
        if not list_response:
            raise NotFound("Player")
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
            The match wasn't available on the server.\n
            This can happen if the match is older than 30 days, or is currently in progress.
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
        ids_list: List[int] = _deduplicate(match_ids)
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
            response = await self.request("getMatchDetailsBatch", ','.join(map(str, chunk_ids)))
            bunched_matches: Dict[int, List[Dict[str, Any]]] = group_by(
                response, lambda mpd: mpd["Match"]
            )
            if expand_players:
                player_ids = []
                for p in response:
                    try:
                        pid = int(p["playerId"])
                    except TypeError as exc:  # pragma: no cover
                        # this usually happens when the API returns an error in ret_msg
                        raise HTTPException(exc, (
                            "Error in the `getMatchDetailsBatch` endpoint!\n"
                            f"Match IDs: {','.join(map(str, chunk_ids))}\n"
                            f"Details: {p['ret_msg']}"
                        ))
                    if pid not in players:  # pragma: no branch
                        player_ids.append(pid)
                players_list = await self.get_players(player_ids)
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
        *,
        start: datetime,
        end: datetime,
        language: Optional[Language] = None,
        reverse: bool = False,
        local_time: bool = False,
        expand_players: bool = False,
    ) -> AsyncGenerator[Match, None]:
        """
        Creates an async generator that lets you iterate over all matches played
        in a particular queue, between the timestamps provided.

        Uses up a single request for every:\n
        • multiple of 10 matches fetched, according to the following points\n
        • 1 day worth of matches fetched, between midnights\n
        • 1 hour worth of matches fetched, between round hours\n
        • 10 minutes worth of matches fetched, between round 10 minutes intervals

        Depending on the timestamps provided, the longest possible fetching interval is used.

        .. note::

            To avoid wasting requests, it's recommended to invoke this generator with timestamps
            representing at least 10 minutes long interval, rounded to the nearest multiple of
            10 minutes. Being more granular will still work, and only return matches that
            fit within the interval specified though.

        .. note::

            Both naive and aware objects are supported for the timestamps.
            Aware objects will be internally converted to UTC according to their timezone.
            Naive objects are assumed to represent UTC time already, unless the ``local_time``
            argument is used.

        Parameters
        ----------
        queue : Queue
            The `Queue` you want to fetch the matches for.
        language : Optional[Language]
            The `Language` you want to fetch the information in.\n
            Default language is used if not provided.
        start : datetime.datetime
            A timestamp indicating the starting point of a time slice you want to
            fetch the matches in.
        end : datetime.datetime
            A timestamp indicating the ending point of a time slice you want to
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
        # process start timestamp
        if start.tzinfo is not None or local_time:
            # assume local timezone, convert into UTC
            start = start.astimezone(timezone.utc).replace(tzinfo=None)
        # process end timestamp
        if end.tzinfo is not None or local_time:
            end = end.astimezone(timezone.utc).replace(tzinfo=None)
        # exit early for a negative interval
        if end < start:
            return
        if language is None:
            language = self._default_language
        # ensure we have champion information first
        await self._ensure_entry(language)
        logger.info(
            f"api.get_matches_for_queue({queue=}, {language=}, {start=} UTC, {end=} UTC, "
            f"{reverse=}, {local_time=}, {expand_players=})"
        )

        # Use the generated date and hour values to iterate over and fetch matches
        players: Dict[int, Player] = {}
        for date, hour in _date_gen(start, end, reverse=reverse):  # pragma: no branch
            response = await self.request("getmatchidsbyqueue", queue.value, date, hour)
            processed: List[Tuple[int, datetime]] = sorted(
                (
                    (int(e["Match"]), _convert_timestamp(e["Entry_Datetime"]))
                    for e in response
                    if e["Active_Flag"] == 'n'
                ),
                key=itemgetter(1),
                reverse=reverse,
            )
            match_ids: List[int] = []
            if reverse:
                for mid, stamp in processed:  # pragma: no branch
                    if stamp < start:
                        break
                    if stamp <= end:
                        match_ids.append(mid)
            else:
                for mid, stamp in processed:  # pragma: no branch
                    if stamp > end:
                        break
                    if stamp >= start:
                        match_ids.append(mid)
            for chunk_ids in chunk(match_ids, 10):  # pragma: no branch
                response = await self.request(
                    "getMatchDetailsBatch", ','.join(map(str, chunk_ids))
                )
                bunched_matches: Dict[int, List[Dict[str, Any]]] = group_by(
                    response, lambda mpd: mpd["Match"]
                )
                if expand_players:
                    player_ids = []
                    for p in response:
                        try:
                            pid = int(p["playerId"])
                        except TypeError as exc:  # pragma: no cover
                            # this usually happens when the API returns an error in ret_msg
                            raise HTTPException(exc, (
                                "Error in the `getMatchDetailsBatch` endpoint!\n"
                                f"Match IDs: {','.join(map(str, chunk_ids))}\n"
                                f"Details: {p['ret_msg']}"
                            ))
                        if pid not in players:  # pragma: no branch
                            player_ids.append(pid)
                    players_dict = await _get_players(self, player_ids)
                    players.update(players_dict)
                chunked_matches = [
                    Match(self, language, match_list, players)
                    for match_list in bunched_matches.values()
                ]
                chunked_matches.sort(key=lambda m: chunk_ids.index(m.id))
                for match in chunked_matches:
                    yield match

    async def get_bounty(
        self, *, language: Optional[Language] = None
    ) -> Tuple[BountyItem, List[BountyItem], List[BountyItem]]:
        """
        Returns a 3-item tuple denoting the (current, upcoming, past) bounty store items, sorted
        by their expiration time.

        .. note:

            The "upcoming" items list is sorted so that the first item is the one
            that is going to appear next, with future items following. The "past" items list
            is sorted so that the first item is the one that has most recently expired,
            with older items following.

        .. note:

            Depending on the bounty store availability, the "current" item may have
            already expired. If this happens, the `BountyItem.active` attribute of
            the "current" item will be `False`, the "upcoming" items list will be empty,
            and the "past" items list will contain the rest, as expected.

        Parameters
        ----------
        language : Optional[Language]
            The `Language` you want to fetch the information in.\n
            Default language is used if not provided.

        Returns
        -------
        Tuple[BountyItem, List[BountyItem], List[BountyItem]]
            An tuple containing the current bounty store item, followed by a list of upcoming
            items, followed by a list of items that have already expired.

        Raises
        ------
        NotFound
            No bounty items were returned.\n
            This can happen if the bounty store is unavailable for a long time.
        """
        if language is None:
            language = self._default_language
        # ensure we have champion information first
        await self._ensure_entry(language)
        response = await self.request("getBountyItems")
        if not response:
            raise NotFound("Bounty items")
        items = [BountyItem(self, language, d) for d in response]
        idx: int = 0
        # find the most recent inactive deal, then go back one index to get the current one
        for i, item in enumerate(items):  # pragma: no branch
            if item.active:
                continue
            # check if Hi-Rez hasn't fucked up and there's at least one active skin,
            # otherwise fall back idx to 0
            if i > 0:  # pragma: no cover
                idx = i-1
            break
        return (items[idx], items[idx-len(items)-1::-1], items[idx+1:])
