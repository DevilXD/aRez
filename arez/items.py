from __future__ import annotations

import re
from typing import Any, Optional, Union, List, Dict, TYPE_CHECKING

from .enums import DeviceType, Language
from .mixins import CacheClient, CacheObject

if TYPE_CHECKING:
    from .cache import DataCache
    from .champion import Champion, Ability
    from .player import PartialPlayer, Player


__all__ = [
    "Device",
    "LoadoutCard",
    "Loadout",
    "MatchItem",
    "MatchLoadout",
]


class Device(CacheObject):
    """
    Represents a Device - those are usually cards, talents and shop items.

    You can find these on the `CacheEntry.devices` attribute.

    Inherits from `CacheObject`.

    Attributes
    ----------
    id : int
        ID of the device.
    name : str
        Name of the device.
    type : DeviceType
        The type of the device.
    raw_description : str
        The raw device's description, possibly containting scale placeholder fields.

        See also: `description`.
    icon_url : str
        The URL of this device's icon.
    ability : Union[Ability, CacheObject]
        The ability this device affects, or a `CacheObject` with only the name set,
        denoting the affected part of the champion.\n
        The usual names you can find here are ``Weapon`` and ``Armor``,
        or ``Unknown`` in cases where this information couldn't be parsed.
    champion : Optional[Union[Champion, CacheObject]]
        The champion this device belongs to.\n
        This is a `CacheObject` with incomplete cache, and `None` for shop items.
    base : float
        The base value of the card's or shop item's scaling.\n
        ``0.0`` for talents.
    scale : float
        The scale value of the card's or shop item's scaling.\n
        ``0.0`` for talents.
    cooldown : int
        The cooldown of this device, in seconds.\n
        ``0`` if there is no cooldown.
    price : int
        The price of this device.\n
        ``0`` if there's no price (it's free).
    unlocked_at : int
        The champion's mastery level required to unlock this device. Applies only to talents.\n
        ``0`` means it's unlocked by default.
    """
    _ability_pattern = re.compile(r'\[(.+?)\] (.*)')
    _scale_pattern = re.compile(r'{scale=(-?\d*\.?\d+)\|(-?\d*\.?\d+)}|{(-?\d+)}')

    def __init__(self, device_data: Dict[str, Any]):
        super().__init__(id=device_data["ItemId"], name=device_data["DeviceName"])
        self.raw_description: str = device_data["Description"].strip()
        self.ability: Union[Ability, CacheObject] = CacheObject()
        match = self._ability_pattern.match(self.raw_description)
        if match:
            self.ability = CacheObject(name=match.group(1))
            self.raw_description = match.group(2)
        self.base: float = 0.0
        self.scale: float = 0.0
        match = self._scale_pattern.search(self.raw_description)
        if match:
            group3 = match.group(3)
            if group3:
                self.base = float(group3)
                self.scale = float(group3)
            else:
                self.base = float(match.group(1))
                self.scale = float(match.group(2))
        item_type = device_data["item_type"]
        if (
            item_type.startswith("Card Vendor Rank")
            or item_type == "Inventory Vendor - Champion Cards"
        ):
            self.type = DeviceType.Card
        elif item_type == "Inventory Vendor - Talents":
            self.type = DeviceType.Talent
        elif item_type.startswith("Burn Card"):
            self.type = DeviceType.Item
        else:
            self.type = DeviceType.Undefined
        # start with None by default
        self.champion: Optional[Union[Champion, CacheObject]] = None
        # if the champion ID is non-zero, replace it with a cache object
        if champion_id := device_data["champion_id"]:
            # later overwritten when the device is added to a champion
            self.champion = CacheObject(id=champion_id)
        self.icon_url: str = device_data["itemIcon_URL"]
        self.cooldown: int = device_data["recharge_seconds"]
        self.price: int = device_data["Price"]
        self.unlocked_at: int = device_data["talent_reward_level"]

    __hash__ = CacheObject.__hash__

    def __repr__(self) -> str:
        return f"{self.type.name}: {self.name}"

    def _attach_champion(self, champion: Champion):
        self.champion = champion
        if type(self.ability) is CacheObject and self.ability.name != "Unknown":
            # upgrade the ability to a full object if possible
            ability = champion.get_ability(self.ability.name)
            if ability:
                self.ability = ability

    @staticmethod
    def _scale_format(value: float) -> str:  # pragma: no cover
        if value % 1 == 0:
            return str(int(value))   # remove .0
        return str(round(value, 3))  # remove floating point math errors

    def description(self, level: int) -> str:
        """
        Formats the item's description, based on the level of the device provided.
        This replaces the scale placeholder fields with the calculated value.

        Parameters
        ----------
        level : int
            The level of the device.\n
            This should range 1-3 for shop items and 1-5 for cards.

        Returns
        -------
        str
            The formatted device's description.
        """
        return self._scale_pattern.sub(
            self._scale_format(self.base + self.scale * level), self.raw_description
        )

class LoadoutCard:
    """
    Represents a Loadout Card.

    Attributes
    ----------
    card : Union[Device, CacheObject]
        The actual card that belongs to this loadout.\n
        `CacheObject` with incomplete cache.
    points : int
        The amount of loadout points that have been assigned to this card.
    """
    def __init__(self, card: Union[Device, CacheObject], points: int):
        self.card: Union[Device, CacheObject] = card
        self.points: int = points

    def __repr__(self) -> str:
        return f"{self.card.name}: {self.points}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.card == other.card and self.points == other.points
        return NotImplemented

    def description(self) -> str:
        """
        The formatted card's description, based on the points assigned.\n
        If the `card` is a `CacheObject`, this will be an empty string.

        :type: str
        """
        if isinstance(self.card, Device):
            return self.card.description(self.points)
        return ''

class Loadout(CacheObject, CacheClient):
    """
    Represents a Champion's Loadout.

    You can get this from the `PartialPlayer.get_loadouts` method.

    Attributes
    ----------
    id : int
        ID of the loadout.
    name : str
        Name of the loadout.
    player : Union[PartialPlayer, Player]
        The player this loadout belongs to.
    champion : Union[Champion, CacheObject]
        The champion this loadout belongs to.\n
        With incomplete cache, this will be a `CacheObject` with the name and ID set.
    language : Language
        The language of all the cards this loadout has.
    cards : List[LoadoutCard]
        A list of loadout cards this loadout consists of.
    """
    def __init__(
        self,
        player: Union[PartialPlayer, Player],
        language: Language,
        loadout_data: Dict[str, Any],
    ):
        assert player.id == loadout_data["playerId"]
        CacheClient.__init__(self, player._api)
        CacheObject.__init__(self, id=loadout_data["DeckId"], name=loadout_data["DeckName"])
        self.player: Union[PartialPlayer, Player] = player
        self.language: Language = language
        champion_id: int = loadout_data["ChampionId"]
        champion: Optional[Union[Champion, CacheObject]] = (
            self._api.get_champion(champion_id, language)
        )
        if champion is None:
            champion = CacheObject(id=champion_id, name=loadout_data["ChampionName"])
        self.champion: Union[Champion, CacheObject] = champion
        self.cards: List[LoadoutCard] = []
        for card_data in loadout_data["LoadoutItems"]:
            card_id: int = card_data["ItemId"]
            card: Optional[Union[Device, CacheObject]] = self._api.get_card(card_id, language)
            if card is None:
                card = CacheObject(id=card_id, name=card_data["ItemName"])
            self.cards.append(LoadoutCard(card, card_data["Points"]))
        self.cards.sort(key=lambda lc: lc.points, reverse=True)

    __hash__ = CacheObject.__hash__

    def __repr__(self) -> str:
        return f"{self.champion.name}: {self.name}"


class MatchItem:
    """
    Represents an item shop's purchase.

    Attributes
    ----------
    item : Union[Device, CacheObject]
        The purchased item.\n
        `CacheObject` with incomplete cache.
    level : int
        The level of the item purchased.
    """
    def __init__(self, item: Union[Device, CacheObject], level: int):
        self.item: Union[Device, CacheObject] = item
        self.level: int = level

    def __repr__(self) -> str:
        return f"{self.item.name}: {self.level}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.item == other.item and self.level == other.level
        return NotImplemented

    def description(self) -> str:
        """
        The formatted item's description, based on it's level.\n
        If the `item` is a `CacheObject`, this will be an empty string.

        :type: str
        """
        if isinstance(self.item, Device):
            return self.item.description(self.level)
        return ''


class MatchLoadout:
    """
    Represents a loadout used in a match.

    Attributes
    ----------
    cards : List[LoadoutCard]
        A list of loadout cards used.\n
        Will be empty if the player hasn't picked a loadout during the match.
    talent : Optional[Union[Device, CacheObject]]
        The talent used.\n
        With incomplete cache, this will be a `CacheObject` with the name and ID set.\n
        `None` when the player hasn't picked a talent during the match.
    """
    def __init__(self, api: DataCache, language: Language, match_data: Dict[str, Any]):
        self.cards: List[LoadoutCard] = []
        for i in range(1, 6):  # 1-5
            card_id: int = match_data[f"ItemId{i}"]
            if not card_id:
                # skip 0s
                continue
            card: Optional[Union[Device, CacheObject]] = api.get_card(card_id, language)
            if card is None:
                if "hasReplay" in match_data:
                    # we're in a full match data
                    card_name = match_data[f"Item_Purch_{i}"]
                else:
                    # we're in a partial (player history) match data
                    card_name = match_data[f"Item_{i}"]
                card = CacheObject(id=card_id, name=card_name)
            self.cards.append(LoadoutCard(card, match_data[f"ItemLevel{i}"]))
        self.cards.sort(key=lambda c: c.points, reverse=True)
        talent_id: int = match_data["ItemId6"]
        if talent_id:
            talent: Optional[Union[Device, CacheObject]] = api.get_talent(talent_id, language)
            if talent is None:
                if "hasReplay" in match_data:
                    # we're in a full match data
                    talent_name = match_data["Item_Purch_6"]
                else:
                    # we're in a partial (player history) match data
                    talent_name = match_data["Item_6"]
                talent = CacheObject(id=talent_id, name=talent_name)
        else:
            talent = None
        self.talent: Optional[Union[Device, CacheObject]] = talent

    def __repr__(self) -> str:
        if not self.talent:  # pragma: no cover
            # This can happen if the player haven't picked a talent / loadout during the match
            return "No Loadout"
        return f"{self.talent.name}: {'/'.join(str(c.points) for c in self.cards)}"
