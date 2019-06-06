from datetime import datetime, timedelta
from typing import Optional, Union, List, Mapping, Iterator

from .items import Device
from .champion import Champion
from .utils import get_name_or_id
from .enumerations import Language, DeviceType

class ChampionInfo:
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
        return filter(lambda d: d.type == DeviceType["Card"], self.devices)

    @property
    def talents(self) -> Iterator[Device]:
        return filter(lambda d: d.type == DeviceType["Talent"], self.devices)

    @property
    def items(self) -> Iterator[Device]:
        return filter(lambda d: d.type == DeviceType["Item"], self.devices)

    def get_champion(self, champion: Union[str, int]) -> Optional[Champion]:
        return get_name_or_id(self.champions, champion)

    def get_card(self, card: Union[str, int]) -> Optional[Device]:
        return get_name_or_id(self.cards, card)

    def get_talent(self, talent: Union[str, int]) -> Optional[Device]:
        return get_name_or_id(self.talents, talent)

    def get_item(self, item: Union[str, int]) -> Optional[Device]:
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
        entry = self._cache.get(language)
        if entry:
            return entry.get_champion(champion)

    def get_card(self, card: Union[str, int], language: Language = Language["english"]) -> Optional[Device]:
        entry = self._cache.get(language)
        if entry:
            return entry.get_card(card)

    def get_talent(self, talent: Union[str, int], language: Language = Language["english"]) -> Optional[Device]:
        entry = self._cache.get(language)
        if entry:
            return entry.get_talent(talent)

    def get_item(self, item: Union[str, int], language: Language = Language["english"]) -> Optional[Device]:
        entry = self._cache.get(language)
        if entry:
            return entry.get_item(item)