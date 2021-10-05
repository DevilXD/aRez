from __future__ import annotations

import asyncio
import logging
from itertools import chain
from datetime import datetime, timedelta
from typing import Any, Optional, Union, List, Dict, TYPE_CHECKING, cast

from .items import Device
from .champion import Champion, Skin
from .endpoint import Endpoint
from .mixins import CacheClient
from .enums import Language, DeviceType
from .utils import group_by, Lookup, WeakValueDefaultDict
from .exceptions import HTTPException, Unavailable, LimitReached

if TYPE_CHECKING:
    from . import responses
    from .champion import Ability


__all__ = [
    "DataCache",
    "CacheEntry",
]
logger = logging.getLogger(__package__)


class DataCache(Endpoint, CacheClient):
    """
    A data cache, cappable of storing multiple cached entires of different languages,
    managing their fetching, refreshing and expiration times.

    Inherits from `Endpoint`.

    .. note::

        You can request your developer ID and authorization key `here.
        <https://fs12.formsite.com/HiRez/form48/secure_index.html>`_

    .. warning::

        The main API class uses this class as base, so all of it's methods are already available
        there. This class is listed here solely for documentation purposes.
        Instanting it yourself is possible, but not recommended.

    Parameters
    ----------
    url : str
        The cache's base endpoint URL.
    dev_id : Union[int, str]
        Your developer's ID (devId).
    auth_key : str
        Your developer's authentication key (authKey).
    enabled : bool
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
        The event loop you want to use for this data cache.\n
        Default loop is used when not provided.
    """
    def __init__(
        self,
        url: str,
        dev_id: Union[int, str],
        auth_key: str,
        *,
        enabled: bool = True,
        initialize: Union[bool, Language] = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(url, dev_id, auth_key, loop=loop)
        CacheClient.__init__(self, self)  # assign CacheClient recursively here
        self._default_language: Language
        if isinstance(initialize, Language):  # pragma: no cover
            self._default_language = initialize
        else:
            self._default_language = Language.English
        self._cache: Dict[Language, CacheEntry] = {}
        self._locks: WeakValueDefaultDict[Any, asyncio.Lock] = WeakValueDefaultDict(
            lambda: asyncio.Lock()
        )
        self.cache_enabled = enabled
        self.refresh_every = timedelta(hours=12)
        if initialize:  # pragma: no cover
            self._loop.create_task(self.initialize())

    # solely for typing, __aexit__ exists in the Endpoint
    async def __aenter__(self) -> DataCache:
        return cast(DataCache, await super().__aenter__())  # pragma: no cover

    def set_default_language(self, language: Language):
        """
        Sets the default language used by the cache in places where one is not provided
        by the user.\n
        The default language set is `Language.English`.

        Parameters
        ----------
        language : Language
            The new default language you want to set.
        """
        if not isinstance(language, Language):
            raise TypeError(
                f"language argument has to be of arez.Language type, got {type(language)}"
            )
        logger.info(f"cache.set_default_language(language={language.name})")
        self._default_language = language

    async def initialize(self, *, language: Optional[Language] = None) -> bool:
        """
        Initializes the data cache, by pre-fetching and storing the `CacheEntry` for the default
        language currently set.

        .. note::

            This will both, force the champion information fetching,
            as well as cache the resulting object.

        Parameters
        ----------
        language : Optional[Language]
            The `Language` you want to initialize the information for.\n
            Default language is used if not provided.

        Returns
        -------
        bool
            `True` if the initialization succeeded without problems, `False` otherwise.
        """
        if language is None:
            language = self._default_language
        logger.info(f"cache.initialize(language={language.name})")
        try:
            entry = await self._fetch_entry(language, force_refresh=True, cache=True)
        # allow Unauthorized to bubble up here; NotFound doesn't apply
        except (HTTPException, Unavailable, LimitReached):  # pragma: no cover
            return False
        return bool(entry)

    async def _fetch_entry(
        self, language: Language, *, force_refresh: bool = False, cache: Optional[bool] = None
    ) -> Optional[CacheEntry]:
        # Use a lock here to ensure no race condition between checking for an entry
        # and setting a new one. Use separate locks per each language.
        async with self._locks[f"cache_fetch_{language.name}"]:
            now = datetime.utcnow()
            entry = self._cache.get(language)
            if not force_refresh and entry is not None and now < entry._expires_at:
                logger.debug(
                    f"cache.fetch_entry(language={language.name}, "
                    f"{force_refresh=}, {cache=}) -> using cached"
                )
                return entry
            logger.debug(
                f"cache.fetch_entry(language={language.name}, "
                f"{force_refresh=}, {cache=}) -> fetching new"
            )
            champions_data = await self.request("getchampions", language.value)
            items_data = await self.request("getitems", language.value)
            skins_data = await self.request("getchampionskins", -1, language.value)
            # Don't strictly enforce skins_data to be there, unless there's no cached entry yet.
            # The reason is: the skins list that's returned right now is quite incomplete,
            # and the only useful information it provides, is Rarity. Failing the whole refresh,
            # just due to the skins list missing, would be quite unfortunate.
            if not champions_data or not items_data or (entry is None and not skins_data):
                logger.debug(
                    f"cache.fetch_entry(language={language.name}, {force_refresh=}, {cache=})"
                    " -> fetching failed, using cached"
                )
                return entry
            expires_at = now + self.refresh_every
            entry = CacheEntry(self, language, expires_at, champions_data, items_data, skins_data)
            logger.debug(
                f"cache.fetch_entry(language={language.name}, {force_refresh=}, {cache=})"
                " -> fetching completed"
            )
            if cache is None:
                cache = self.cache_enabled
            if cache:
                self._cache[language] = entry
        return entry

    async def _ensure_entry(self, language: Optional[Language]) -> Optional[CacheEntry]:
        if language is None:
            language = self._default_language
        if not self.cache_enabled:
            return self.get_entry(language)
        logger.debug(f"cache.ensure_entry(language={language.name})")
        entry = await self._fetch_entry(language)
        return entry

    def get_entry(self, language: Optional[Language] = None) -> Optional[CacheEntry]:
        """
        Returns a cache entry for the given language specified.

        .. note::

            This method can return `None` or stale data if the entry hasn't been fetched yet,
            or haven't been updated in a while.\n
            Consider using the `get_champion_info` method from the main API instead.

        Parameters
        ----------
        language : Optional[Language]
            The `Language` you want to get the entry in.\n
            Default language is used if not provided.

        Returns
        -------
        Optional[CacheEntry]
            The cache entry you requested.\n
            `None` is returned if the entry for the language specified hasn't been fetched yet.
        """
        if language is None:
            language = self._default_language
        logger.info(f"cache.get_entry(language={language.name})")
        return self._cache.get(language)


class CacheEntry:
    """
    Represents a collection of champions, cards, talents and shop items.
    You can get this one from the `PaladinsAPI.get_champion_info` or `DataCache.get_entry` methods.

    .. note::

        The `Lookup` class provides an easy way of searching for a particular object,
        based on its Name or ID. You can also obtain a list of all objects instead.

        Please see the example code below:

        .. code-block:: py

            entry: CacheEntry

            # obtain a list of all champions
            champions = list(entry.champions)
            # get a particular champion by their name
            champion = entry.champions.get("Androxus")
            # fuzzy name matching
            champion = entry.champions.get_fuzzy("andro")

    Attributes
    ----------
    language : Language
        The language of this entry.
    champions : Lookup[Champion]
        An object that lets you iterate over all champions.
    abilities : Lookup[Ability]
        An object that lets you iterate over all champion's abilities.
    skins : Lookup[Skin]
        An object that lets you iterate over all champion's skins.
    items : Lookup[Device]
        An object that lets you iterate over all shop items.
    cards : Lookup[Device]
        An object that lets you iterate over all cards.
    talents : Lookup[Device]
        An object that lets you iterate over all talents.
    devices : Lookup[Device]
        An object that lets you iterate over all devices (shop items, cards and talents).
    """
    def __init__(
        self,
        cache: DataCache,
        language: Language,
        expires_at: datetime,
        champions_data: List[responses.ChampionObject],
        items_data: List[responses.DeviceObject],
        skins_data: List[responses.ChampionSkinObject],
    ):
        self._cache = cache
        self.language = language
        self._expires_at = expires_at
        # process devices (shop items, cards and talents)
        sorted_devices: Dict[int, List[Device]] = {}
        items = []
        cards = []
        talents = []
        for device_data in items_data:
            device = Device(device_data)
            device_type = device.type
            if device_type == DeviceType.Undefined:
                # skip invalid / unknown devices
                continue
            sorted_devices.setdefault(device_data["champion_id"], []).append(device)
            if device_type == DeviceType.Card:
                cards.append(device)
            elif device_type == DeviceType.Talent:
                talents.append(device)
            elif device_type == DeviceType.Item:  # pragma: no branch
                items.append(device)
        self.items: Lookup[Device, Device] = Lookup(items)
        self.cards: Lookup[Device, Device] = Lookup(cards)
        self.talents: Lookup[Device, Device] = Lookup(talents)
        self.devices: Lookup[Device, Device] = Lookup(chain(items, talents, cards))
        # pre-process skins (sort per champion)
        skins = group_by(skins_data, key=lambda s: s["champion_id"])
        # process champions
        self.champions: Lookup[Champion, Champion] = Lookup(
            Champion(
                self._cache,
                language,
                champ_data,
                sorted_devices.get(champ_data["id"], []),
                skins.get(champ_data["id"], []),
            )
            for champ_data in champions_data
        )
        # process abilities
        self.abilities: Lookup[Ability, Ability] = Lookup(
            ability for champion in self.champions for ability in champion.abilities
        )
        # process skins
        self.skins: Lookup[Skin, Skin] = Lookup(
            skin for champion in self.champions for skin in champion.skins
        )
        logger.debug(
            f"CacheEntry(language={language.name}, expires_at={self._expires_at}, "
            f"len(champions)={len(self.champions)}, len(devices)={len(self.devices)}, "
            f"len(items)={len(self.items)}, len(cards)={len(self.cards)}, "
            f"len(talents)={len(self.talents)}, len(skins)={len(self.skins)}) -> created"
        )
