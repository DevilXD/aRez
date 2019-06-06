from typing import Union, List, TYPE_CHECKING

from .utils import get_name_or_id
from .enumerations import Language, DeviceType, AbilityType

class Ability:

    def __init__(self, ability_data):
        self.name = ability_data["Summary"]
        self.id = ability_data["Id"]
        self.description = ability_data["Description"].strip().replace('\r', ' ').replace('  ', ' ')
        self.type = AbilityType.get(ability_data["damageType"]) or AbilityType.get(0) #pylint: disable=no-member
        self.cooldown = ability_data["rechargeSeconds"]
        self.icon_url = ability_data["URL"]

class Champion:

    def __init__(self, devices: List['Device'], champion_data: dict):
        self.name = champion_data["Name"]
        self.id = champion_data["id"]
        self.title = champion_data["Title"]
        self.role = champion_data["Roles"][9:].replace("er", "")
        self.icon_url = champion_data["ChampionIcon_URL"]
        self.lore = champion_data["Lore"]
        self.health = champion_data["Health"]
        self.speed = champion_data["Speed"]

        self.abilities = [Ability(champion_data[a]) for a in champion_data if a.startswith("Ability_")]
        self.talents: List['Device'] = []
        self.cards: List['Device'] = []

        for d in devices:
            if d.type == DeviceType["Undefined"]:
                continue
            elif d.type == DeviceType["Card"]:
                self.cards.append(d)
            elif d.type == DeviceType["Talent"]:
                self.talents.append(d)
            d._attach_champion(self)
        self.talents.sort(key=lambda d: d.unlocked_at)
        self.cards.sort(key=lambda d: d.ability)
    
    def __eq__(self, other) -> bool:
        assert isinstance(other, self.__class__)
        return self.id == other.id
    
    def __repr__(self) -> str:
        return "{0.__class__.__name__}({0.name}:{0.id})".format(self)
    
    def __bool__(self) -> bool:
        return len(self.cards) == 16 and len(self.talents) == 3
    
    def get_card(self, card: Union[str, int]) -> 'Device':
        return get_name_or_id(self.cards, card)
    
    def get_talent(self, talent: Union[str, int]) -> 'Device':
        return get_name_or_id(self.talents, talent)
