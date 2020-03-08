from datetime import datetime, timedelta
from typing import Optional, Union, List, Dict, Iterator, TYPE_CHECKING

from .items import Device
from .utils import Lookup
from .mixins import APIClient
from .champion import Champion, Ability
from .enumerations import Language, DeviceType


if TYPE_CHECKING:
    from .api import PaladinsAPI


class ChampionInfo:
    """
    Represents a collection of champions, cards, talents and shop items.
    You can get this one from the `PaladinsAPI.get_champion_info` or `DataCache.get_entry` methods.

    Attributes
    ----------
    language : Language
        The language of this entry.
    champions : Lookup[Champion]
        An object that lets you iterate over all champions.\n
        Use ``list()`` to get a list instead.
    abilities : Lookup[Ability]
        An object that lets you iterate over all champion's abilities.\n
        Use ``list()`` to get a list instead.
    devices : Lookup[Device]
        An object that lets you iterate over all devices (cards, talents and shop items).\n
        This also includes other devices that are returned from the API,
        but are considered invalid.\n
        Use ``list()`` to get a list instead.
    """
    def __init__(
        self, language: Language, expires_at: datetime, champions_data: dict, items_data: dict
    ):
        self.language = language
        self._expires_at = expires_at
        sorted_devices: Dict[int, List[Device]] = {}
        for d in items_data:
            champ_list = sorted_devices.setdefault(d["champion_id"], [])
            champ_list.append(Device(d))
        self.devices: Lookup[Device] = Lookup(d for dl in sorted_devices.values() for d in dl)
        self.champions: Lookup[Champion] = Lookup(
            Champion(sorted_devices.get(c["id"], []), c) for c in champions_data
        )
        self.abilities: Lookup[Ability] = Lookup(
            a for c in self.champions for a in c.abilities
        )

    @property
    def cards(self) -> Iterator[Device]:
        """
        A filtered iterator that lets you iterate over all cards.

        Use ``list()`` to get a list instead.
        """
        dt = DeviceType["Card"]
        return filter(lambda d: d.type == dt, self.devices)

    @property
    def talents(self) -> Iterator[Device]:
        """
        A filtered iterator that lets you iterate over all talents.

        Use ``list()`` to get a list instead.
        """
        dt = DeviceType["Talent"]
        return filter(lambda d: d.type == dt, self.devices)

    @property
    def items(self) -> Iterator[Device]:
        """
        A filtered iterator that lets you iterate over all shop items.

        Use ``list()`` to get a list instead.
        """
        dt = DeviceType["Item"]
        return filter(lambda d: d.type == dt, self.devices)

    def get_champion(
        self, champion: Union[str, int], *, fuzzy: bool = False
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
        return self.champions.lookup(champion, fuzzy=fuzzy)

    def get_card(self, card: Union[str, int], *, fuzzy: bool = False) -> Optional[Device]:
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
        return self.devices.lookup(card, fuzzy=fuzzy)

    def get_talent(self, talent: Union[str, int], *, fuzzy: bool = False) -> Optional[Device]:
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
        return self.devices.lookup(talent, fuzzy=fuzzy)

    def get_item(self, item: Union[str, int], *, fuzzy: bool = False) -> Optional[Device]:
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
        return self.devices.lookup(item, fuzzy=fuzzy)


class DataCache(APIClient):
    def __init__(self, api: "PaladinsAPI"):
        super().__init__(api)
        self._cache: Dict[Language, ChampionInfo] = {}
        self.refresh_every = timedelta(hours=12)

    async def _fetch_entry(self, language: Language, *, force_refresh: bool = False):
        now = datetime.utcnow()
        entry = self._cache.get(language)
        if entry is None or now >= entry._expires_at or force_refresh:
            champions_data = await self._api.request("getgods", language.value)
            items_data = await self._api.request("getitems", language.value)
            if champions_data and items_data:
                expires_at = now + self.refresh_every
                entry = self._cache[language] = ChampionInfo(
                    language, expires_at, champions_data, items_data
                )
        return entry

    def get_entry(self, language: Optional[Language] = None) -> Optional[ChampionInfo]:
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
        Optional[ChampionInfo]
            The cache entry you requested.\n
            `None` is returned if the entry for the language specified hasn't been fetched yet.
        """
        if language is None:
            language = self._api._default_language
        return self._cache.get(language)

    def get_champion(
        self,
        champion: Union[str, int],
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
            language = self._api._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_champion(champion, fuzzy=fuzzy)
        return None

    def get_card(
        self,
        card: Union[str, int],
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
            language = self._api._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_card(card, fuzzy=fuzzy)
        return None

    def get_talent(
        self,
        talent: Union[str, int],
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
            language = self._api._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_talent(talent, fuzzy=fuzzy)
        return None

    def get_item(
        self,
        item: Union[str, int],
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
            language = self._api._default_language
        entry = self._cache.get(language)
        if entry:
            return entry.get_item(item, fuzzy=fuzzy)
        return None
