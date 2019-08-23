import re
from typing import Optional, Union

from .champion import Champion, Ability
from .enumerations import DeviceType, Language

class Device:
    """
    Represents a Device - those are usually cards, talents and shop items.
    
    Attributes
    ----------
    id : int
        ID of the device.
    name : str
        Name of the device.
    type : DeviceType
        The type of the device.
    description : str
        The device's description.
    icon_url : str
        The URL of this device's icon.
    ability : Optional[Union[Ability, str]]
        The ability this device affects, or a string denoting the affected part of the champion.
        None for shop items.
    champion : Optional[Champion]
        The champion this device belongs to.
        None for shop items.
    cooldown : int
        The cooldown of this device, in seconds.
        0 if there is no cooldown.
    price : int
        The price of this device.
        0 if there's no price (it's free).
    unlocked_at : int
        The champion's mastery level required to unlock this device. Applies only to talents.
        0 means it's inlocked by default.
    """
    _desc_pattern = re.compile(r'\[(.+?)\] (.*)')

    def __init__(self, device_data: dict):
        desc = device_data["Description"].strip()
        match = self._desc_pattern.match(desc)
        if match:
            ability = match.group(1)
            desc = match.group(2)
        else:
            ability = None
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
        return "{0.type.name}: {0.name}".format(self)
    
    def _attach_champion(self, champion: Champion):
        self.champion = champion
        ability = champion.get_ability(self.ability)
        if ability:
            self.ability = ability

class LoadoutCard:
    """
    Represents a Loadout Card.
    
    Attributes
    ----------
    card : Device
        The actual card that belongs to this loadout.
    points : int
        The amount of loadout points that have been assigned to this card.
    """
    def __init__(self, card: Device, points: int):
        self.card = card
        self.points = points
    
    def __repr__(self) -> str:
        return "{0.card.name}: {0.points}".format(self)

class Loadout:
    """
    Represents a Champion's Loadout.
    
    Attributes
    ----------
    id : int
        ID of the loadout.
    name : str
        Name of the loadout.
    player : Union[PartialPlayer, Player]
        The player this loadout belongs to.
    champion : Champion
        The champion this loadout belongs to.
    language : Language
        The language of all the cards this loadout has.
    cards : List[LoadoutCard]
        A list of loadout cards this lodaout consists of.
    """
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
