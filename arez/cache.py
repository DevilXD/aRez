from __future__ import annotations

import asyncio
import logging
from itertools import chain
from datetime import datetime, timedelta
from typing import Any, Optional, Union, List, Dict, TYPE_CHECKING

from .items import Device
from .champion import Champion
from .endpoint import Endpoint
from .mixins import CacheClient
from .enums import Language, DeviceType
from .utils import Lookup, WeakValueDefaultDict
from .exceptions import Unavailable, HTTPException

if TYPE_CHECKING:
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
            self.loop.create_task(self.initialize())

    # solely for typing, __aexit__ exists in the Endpoint
    async def __aenter__(self) -> DataCache:
        return self  # pragma: no cover

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
        assert isinstance(language, Language)
        logger.info(f"cache.set_default_language({language=})")
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
        logger.info(f"cache.initialize({language=})")
        try:
            entry = await self._fetch_entry(language, force_refresh=True, cache=True)
        except (HTTPException, Unavailable):  # pragma: no cover
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
            if entry is None or now >= entry._expires_at or force_refresh:
                champions_data = await self.request("getgods", language.value)
                items_data = await self.request("getitems", language.value)
                if champions_data and items_data:
                    expires_at = now + self.refresh_every
                    entry = CacheEntry(
                        self, language, expires_at, champions_data, items_data
                    )
                    if cache is None:
                        cache = self.cache_enabled
                    if cache:
                        self._cache[language] = entry
        return entry

    async def _ensure_entry(self, language: Language):
        if not self.cache_enabled:
            return
        logger.debug(f"cache.ensure_entry({language=})")
        await self._fetch_entry(language)

    def get_entry(self, language: Optional[Language] = None) -> Optional[CacheEntry]:
        """
        Returns a cache entry for the given language specified.

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
        logger.info(f"cache.get_entry({language=})")
        return self._cache.get(language)

    def get_champion(
        self,
        champion: Union[str, int],
        /,
        language: Optional[Language] = None,
        *,
        fuzzy: bool = False,
    ) -> Optional[Champion]:
        """
        Returns a champion for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return `None` or stale data if the entry hasn't been fetched yet,
        or haven't been updated in a while.\n
        Consider using the `get_champion_info` method from the main API instead.

        Parameters
        ----------
        champion : Union[str, int]
            The Name or ID of the champion you want to get.
        language : Optional[Language]
            The `Language` you want to get the champion in.\n
            Default language is used if not provided.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Champion]
            The champion you requested.\n
            `None` is returned if a champion couldn't be found, or the entry for the language
            specified hasn't been fetched yet.
        """
        if language is None:
            language = self._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_champion(champion, fuzzy=fuzzy)
        return None

    def get_card(
        self,
        card: Union[str, int],
        /,
        language: Optional[Language] = None,
        *,
        fuzzy: bool = False,
    ) -> Optional[Device]:
        """
        Returns a card for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return `None` or stale data if the entry hasn't been fetched yet,
        or haven't been updated in a while.\n
        Consider using the `get_champion_info` method from the main API instead.

        Parameters
        ----------
        card : Union[str, int]
            The Name or ID of the card you want to get.
        language : Optional[Language]
            The `Language` you want to get the card in.\n
            Default language is used if not provided.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The card you requested.\n
            `None` is returned if a card couldn't be found, or the entry for the language
            specified hasn't been fetched yet.
        """
        if language is None:
            language = self._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_card(card, fuzzy=fuzzy)
        return None

    def get_talent(
        self,
        talent: Union[str, int],
        /,
        language: Optional[Language] = None,
        *,
        fuzzy: bool = False,
    ) -> Optional[Device]:
        """
        Returns a talent for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return `None` or stale data if the entry hasn't been fetched yet,
        or haven't been updated in a while.\n
        Consider using the `get_champion_info` method from the main API instead.

        Parameters
        ----------
        talent : Union[str, int]
            The Name or ID of the talent you want to get.
        language : Optional[Language]
            The `Language` you want to get the talent in.\n
            Default language is used if not provided.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The talent you requested.\n
            `None` is returned if a talent couldn't be found, or the entry for the language
            specified hasn't been fetched yet.\n
        """
        if language is None:
            language = self._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_talent(talent, fuzzy=fuzzy)
        return None

    def get_item(
        self,
        item: Union[str, int],
        /,
        language: Optional[Language] = None,
        *,
        fuzzy: bool = False,
    ) -> Optional[Device]:
        """
        Returns a shop item for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return `None` or stale data if the entry hasn't been fetched yet,
        or haven't been updated in a while.\n
        Consider using the `get_champion_info` method from the main API instead.

        Parameters
        ----------
        item : Union[str, int]
            The Name or ID of the item you want to get.
        language : Optional[Language]
            The `Language` you want to get the shop item in.\n
            Default language is used if not provided.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The shop item you requested.\n
            `None` is returned if a shop item couldn't be found, or the entry for the language
            specified hasn't been fetched yet.
        """
        if language is None:
            language = self._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_item(item, fuzzy=fuzzy)
        return None

    def get_device(
        self,
        device: Union[str, int],
        /,
        language: Optional[Language] = None,
        *,
        fuzzy: bool = False,
    ) -> Optional[Device]:
        """
        Returns a device for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return `None` or stale data if the entry hasn't been fetched yet,
        or haven't been updated in a while.\n
        Consider using the `get_champion_info` method from the main API instead.

        Parameters
        ----------
        device : Union[str, int]
            The Name or ID of the item you want to get.
        language : Optional[Language]
            The `Language` you want to get the device in.\n
            Default language is used if not provided.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The device you requested.\n
            `None` is returned if a device couldn't be found, or the entry for the language
            specified hasn't been fetched yet.
        """
        if language is None:
            language = self._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_device(device, fuzzy=fuzzy)
        return None


class CacheEntry:
    """
    Represents a collection of champions, cards, talents and shop items.
    You can get this one from the `PaladinsAPI.get_champion_info` or `DataCache.get_entry` methods.

    Attributes
    ----------
    language : Language
        The language of this entry.
    champions : Lookup[Champion]
        An object that lets you iterate over all champions.\n
        Use ``list(...)`` to get a list instead.
    abilities : Lookup[Ability]
        An object that lets you iterate over all champion's abilities.\n
        Use ``list(...)`` to get a list instead.
    items : Lookup[Device]
        An object that lets you iterate over all shop items.\n
        Use ``list(...)`` to get a list instead.
    cards : Lookup[Device]
        An object that lets you iterate over all cards.\n
        Use ``list(...)`` to get a list instead.
    talents : Lookup[Device]
        An object that lets you iterate over all talents.\n
        Use ``list(...)`` to get a list instead.
    devices : Lookup[Device]
        An object that lets you iterate over all devices (shop items, cards and talents).\n
        Use ``list(...)`` to get a list instead.
    """
    def __init__(
        self,
        cache: DataCache,
        language: Language,
        expires_at: datetime,
        champions_data: dict,
        items_data: dict,
    ):
        self._cache = cache
        self.language = language
        self._expires_at = expires_at
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
        self.items: Lookup[Device] = Lookup(items)
        self.cards: Lookup[Device] = Lookup(cards)
        self.talents: Lookup[Device] = Lookup(talents)
        self.devices: Lookup[Device] = Lookup(chain(items, talents, cards))
        self.champions: Lookup[Champion] = Lookup(
            Champion(
                self._cache, language, sorted_devices.get(champ_data["id"], []), champ_data
            )
            for champ_data in champions_data
        )
        self.abilities: Lookup[Ability] = Lookup(
            ability for champion in self.champions for ability in champion.abilities
        )
        logger.debug(
            f"CacheEntry({language=}, expires_at={self._expires_at}, "
            f"len(champions)={len(self.champions)}, len(devices)={len(self.devices)}, "
            f"len(items)={len(self.items)}, len(cards)={len(self.cards)}, "
            f"len(talents)={len(self.talents)}) -> created"
        )

    def get_champion(
        self, champion: Union[str, int], /, *, fuzzy: bool = False
    ) -> Optional[Champion]:
        """
        Returns a champion for the given Name or ID.
        Case sensitive.

        Parameters
        ----------
        champion : Union[str, int]
            The Name or ID of the champion you want to get.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Champion]
            The champion you requested.\n
            `None` is returned if a champion with the requested Name or ID couldn't be found.
        """
        return self.champions._lookup(champion, fuzzy=fuzzy)

    def get_card(self, card: Union[str, int], /, *, fuzzy: bool = False) -> Optional[Device]:
        """
        Returns a champion's card for the given Name or ID.
        Case sensitive.

        Parameters
        ----------
        card : Union[str, int]
            The Name or ID of the card you want to get.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The card you requested.\n
            `None` is returned if a card with the requested Name or ID couldn't be found.
        """
        return self.cards._lookup(card, fuzzy=fuzzy)

    def get_talent(self, talent: Union[str, int], /, *, fuzzy: bool = False) -> Optional[Device]:
        """
        Returns a champion's talent for the given Name or ID.
        Case sensitive.

        Parameters
        ----------
        talent : Union[str, int]
            The Name or ID of the talent you want to get.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The talent you requested.\n
            `None` is returned if a talent with the requested Name or ID couldn't be found.
        """
        return self.talents._lookup(talent, fuzzy=fuzzy)

    def get_item(self, item: Union[str, int], /, *, fuzzy: bool = False) -> Optional[Device]:
        """
        Returns a shop item for the given Name or ID.
        Case sensitive.

        Parameters
        ----------
        item : Union[str, int]
            The Name or ID of the shop item you want to get.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The shop item you requested.\n
            `None` is returned if a shop item with the requested Name or ID couldn't be found.
        """
        return self.items._lookup(item, fuzzy=fuzzy)

    def get_device(self, device: Union[str, int], /, *, fuzzy: bool = False) -> Optional[Device]:
        """
        Returns a device for the given Name or ID.
        Case sensitive.

        Parameters
        ----------
        device : Union[str, int]
            The Name or ID of the device you want to get.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The device you requested.\n
            `None` is returned if a device with the requested Name or ID couldn't be found.
        """
        return self.devices._lookup(device, fuzzy=fuzzy)
