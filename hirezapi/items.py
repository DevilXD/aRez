import re
from typing import Union

from .champion import Champion
from .enumerations import DeviceType, Language

class Device:

    _desc_pattern = re.compile(r'\[(.+?)\] (.*)')

    def __init__(self, device_data: dict):
        desc = device_data["Description"].strip()
        match = self._desc_pattern.match(desc)
        if match:
            ability = match.group(1)
            desc = match.group(2)
        else:
            ability = '-'
        if device_data["item_type"] == "Inventory Vendor - Talents":
            self.type = DeviceType["Talent"]
        elif device_data["item_type"].startswith("Card Vendor Rank"):
            self.type = DeviceType["Card"]
        elif device_data["item_type"].startswith("Burn Card"):
            self.type = DeviceType["Item"]
        else:
            self.type = DeviceType["Undefined"]
        self.champion = None # later overwritten when the device is added to a champion
        self.name = device_data["DeviceName"]
        self.ability = ability
        self.description = desc
        self.id = device_data["ItemId"]
        self.icon_url = device_data["itemIcon_URL"]
        self.cooldown = device_data["recharge_seconds"]
        self.price = device_data["Price"]
        self.unlocked_at = device_data["talent_reward_level"]
    
    def __eq__(self, other) -> bool:
        assert isinstance(other, self.__class__)
        return self.id == other.id

    def __repr__(self) -> str:
        return "{}: {}".format(self.type.name, self.name)
    
    def _attach_champion(self, champion: Champion):
        self.champion = champion

class LoadoutCard:
    def __init__(self, card: Device, points: int):
        self.card = card
        self.points = points
    
    def __repr__(self) -> str:
        return "{0.card.name}: {0.points}".format(self)

class Loadout:
    def __init__(self, player: Union['PartialPlayer', 'Player'], language: Language, loadout_data: dict):
        assert player.id == loadout_data["playerId"]
        self._api = player._api
        self.player = player
        self.language = language
        self.champion = self._api.get_champion(loadout_data["ChampionId"], language)
        self.name = loadout_data["DeckName"]
        self.id = loadout_data["DeckId"]
        self.cards = [LoadoutCard(self._api.get_card(c["ItemId"], language), c["Points"]) for c in loadout_data["LoadoutItems"]]
    
    def __repr__(self) -> str:
        return "{0.champion.name}: {0.name}".format(self)
