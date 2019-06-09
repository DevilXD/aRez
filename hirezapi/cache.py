from datetime import datetime, timedelta
from typing import Optional, Union, List, Mapping, Iterator

from .items import Device
from .champion import Champion
from .utils import get_name_or_id
from .enumerations import Language, DeviceType

class ChampionInfo:
    """
    Represents a collection of champions, cards, telants and shop items.
    
    Attributes
    ----------
    language : Language
        The language of this entry.
    devices : List[Device]
        Returns a list of all cards, talents and shop items.
        This list also contains other devices that are returned from the API,
        but are considered invalid.
    champions : List[Champion]
        Returns a list of all champions.
    """
    def __init__(self, cache, language, champions_data, items_data):
        self.language = language
        self._expires_at = datetime.utcnow() + cache.refresh_every
        sorted_devices = {}
        for d in items_data:
            champ_id = d["champion_id"]
            if champ_id not in sorted_devices:
                sorted_devices[champ_id] = []
            sorted_devices[champ_id].append(Device(d))
        self.devices = [d for c in sorted_devices for d in sorted_devices[c]]
        self.champions = [Champion(sorted_devices.get(c["id"], []), c) for c in champions_data]

    @property
    def cards(self) -> Iterator[Device]:
        """
        A filtered iterator that lets iterate over all cards.

        Use `list()` to get a list instead.
        """
        return filter(lambda d: d.type == DeviceType["Card"], self.devices)

    @property
    def talents(self) -> Iterator[Device]:
        """
        A filtered iterator that lets iterate over all talents.

        Use `list()` to get a list instead.
        """
        return filter(lambda d: d.type == DeviceType["Talent"], self.devices)

    @property
    def items(self) -> Iterator[Device]:
        """
        A filtered iterator that lets iterate over all shop items.

        Use `list()` to get a list instead.
        """
        return filter(lambda d: d.type == DeviceType["Item"], self.devices)

    def get_champion(self, champion: Union[str, int]) -> Optional[Champion]:
        """
        Returns a champion for the given Name or ID.
        Case sensitive.
        
        Parameters
        ----------
        champion : Union[str, int]
            The Name or ID of the champion you want to get.
        
        Returns
        -------
        Optional[Champion]
            The champion you requested.
            None is returned if a champion with the requested Name or ID couldn't be found.
        """
        return get_name_or_id(self.champions, champion)

    def get_card(self, card: Union[str, int]) -> Optional[Device]:
        """
        Returns a champion's card for the given Name or ID.
        Case sensitive.
        
        Parameters
        ----------
        card : Union[str, int]
            The Name or ID of the card you want to get.
        
        Returns
        -------
        Optional[Device]
            The card you requested.
            None is returned if a card with the requested Name or ID couldn't be found.
        """
        return get_name_or_id(self.cards, card)

    def get_talent(self, talent: Union[str, int]) -> Optional[Device]:
        """
        Returns a champion's talent for the given Name or ID.
        Case sensitive.
        
        Parameters
        ----------
        talent : Union[str, int]
            The Name or ID of the talent you want to get.
        
        Returns
        -------
        Optional[Device]
            The talent you requested.
            None is returned if a talent with the requested Name or ID couldn't be found.
        """
        return get_name_or_id(self.talents, talent)

    def get_item(self, item: Union[str, int]) -> Optional[Device]:
        """
        Returns a shop item for the given Name or ID.
        Case sensitive.
        
        Parameters
        ----------
        item : Union[str, int]
            The Name or ID of the shop item you want to get.
        
        Returns
        -------
        Optional[Device]
            The shop item you requested.
            None is returned if a shop item with the requested Name or ID couldn't be found.
        """
        return get_name_or_id(self.items, item)

class DataCache:
    def __init__(self):
        self._cache: Mapping[Language, ChampionInfo] = {}
        self.refresh_every = timedelta(hours=12)

    def __setitem__(self, language: Language, info_init_tuple):
        if not isinstance(language, Language):
            raise IndexError("Only Language emumeration members are allowed as keys")
        self._cache[language] = ChampionInfo(self, language, *info_init_tuple)

    def __getitem__(self, language: Language):
        return self._cache.get(language)

    def _needs_refreshing(self, language: Language = Language["english"]) -> bool:
        entry = self._cache.get(language)
        if entry is None or datetime.utcnow() >= entry._expires_at:
            return True
        return False

    def get_champion(self, champion: Union[str, int], language: Language = Language["english"]) -> Optional[Champion]:
        """
        Returns a champion for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return None or stale data if the entry hasn't been fetched yet, or haven't been updated in a while.
        Consider using the `get_champion_info` method from the main API instead.
        
        Parameters
        ----------
        champion : Union[str, int]
            The Name or ID of the champion you want to get.
        language : Language, optional
            The Language you want to get the champion in.
            Defaults to Language["english"].
        
        Returns
        -------
        Optional[Champion]
            The champion you requested.
            None is returned if a champion couldn't be found, or the entry for the language specified hasn't been fetched yet.
        """
        entry = self._cache.get(language)
        if entry:
            return entry.get_champion(champion)

    def get_card(self, card: Union[str, int], language: Language = Language["english"]) -> Optional[Device]:
        """
        Returns a card for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return None or stale data if the entry hasn't been fetched yet, or haven't been updated in a while.
        Consider using the `get_champion_info` method from the main API instead.
        
        Parameters
        ----------
        card : Union[str, int]
            The Name or ID of the card you want to get.
        language : Language, optional
            The Language you want to get the card in.
            Defaults to Language["english"].
        
        Returns
        -------
        Optional[Device]
            The card you requested.
            None is returned if a card couldn't be found, or the entry for the language specified hasn't been fetched yet.
        """
        entry = self._cache.get(language)
        if entry:
            return entry.get_card(card)

    def get_talent(self, talent: Union[str, int], language: Language = Language["english"]) -> Optional[Device]:
        """
        Returns a talent for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return None or stale data if the entry hasn't been fetched yet, or haven't been updated in a while.
        Consider using the `get_champion_info` method from the main API instead.
        
        Parameters
        ----------
        talent : Union[str, int]
            The Name or ID of the talent you want to get.
        language : Language, optional
            The Language you want to get the talent in.
            Defaults to Language["english"].
        
        Returns
        -------
        Optional[Device]
            The talent you requested.
            None is returned if a talent couldn't be found, or the entry for the language specified hasn't been fetched yet.
        """
        entry = self._cache.get(language)
        if entry:
            return entry.get_talent(talent)

    def get_item(self, item: Union[str, int], language: Language = Language["english"]) -> Optional[Device]:
        """
        Returns a shop item for the given Name or ID, and Language specified.
        Case sensitive.

        This method can return None or stale data if the entry hasn't been fetched yet, or haven't been updated in a while.
        Consider using the `get_champion_info` method from the main API instead.
        
        Parameters
        ----------
        item : Union[str, int]
            The Name or ID of the item you want to get.
        language : Language, optional
            The Language you want to get the shop item in.
            Defaults to Language["english"].
        
        Returns
        -------
        Optional[Device]
            The shop item you requested.
            None is returned if a shop item couldn't be found, or the entry for the language specified hasn't been fetched yet.
        """
        entry = self._cache.get(language)
        if entry:
            return entry.get_item(item)