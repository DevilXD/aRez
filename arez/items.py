from __future__ import annotations

import re
from typing import cast, TYPE_CHECKING

from . import responses
from .enums import DeviceType, Passive
from .mixins import CacheClient, CacheObject

if TYPE_CHECKING:
    from .cache import CacheEntry
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
    ability : Ability | CacheObject
        The ability this device affects, or a `CacheObject` with only the name set,
        denoting the affected part of the champion.\n
        The usual names you can find here are ``Weapon`` and ``Armor``,
        or ``Unknown`` in cases where this information couldn't be parsed.
    champion : Champion | CacheObject | None
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

    def __init__(self, device_data: responses.DeviceObject):
        super().__init__(id=device_data["ItemId"], name=device_data["DeviceName"])
        self.raw_description: str = device_data["Description"].strip()
        self.ability: Ability | CacheObject = CacheObject()
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
        self.champion: Champion | CacheObject | None = None
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
            ability = champion.abilities.get(self.ability.name)
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
            self._scale_format(self.base + self.scale * (level - 1)), self.raw_description
        )


class LoadoutCard:
    """
    Represents a Loadout Card.

    Attributes
    ----------
    card : Device | CacheObject
        The actual card that belongs to this loadout.\n
        `CacheObject` with incomplete cache.
    points : int
        The amount of loadout points that have been assigned to this card.
    """
    def __init__(self, card: Device | CacheObject, points: int):
        self.card: Device | CacheObject = card
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
    player : PartialPlayer | Player
        The player this loadout belongs to.
    champion : Champion | CacheObject
        The champion this loadout belongs to.\n
        With incomplete cache, this will be a `CacheObject` with the name and ID set.
    cards : list[LoadoutCard]
        A list of loadout cards this loadout consists of.
    """
    def __init__(
        self,
        player: PartialPlayer | Player,
        cache_entry: CacheEntry | None,
        loadout_data: responses.ChampionLoadoutObject,
    ):
        assert player.id == loadout_data["playerId"]
        CacheClient.__init__(self, player._api)
        CacheObject.__init__(self, id=loadout_data["DeckId"], name=loadout_data["DeckName"])
        self.player: PartialPlayer | Player = player
        champion: Champion | CacheObject | None = None
        if cache_entry is not None:
            champion = cache_entry.champions.get(loadout_data["ChampionId"])
        if champion is None:
            champion = CacheObject(
                id=loadout_data["ChampionId"], name=loadout_data["ChampionName"]
            )
        self.champion: Champion | CacheObject = champion
        self.cards: list[LoadoutCard] = []
        for card_data in loadout_data["LoadoutItems"]:
            card: Device | CacheObject | None = None
            if cache_entry is not None:
                card = cache_entry.cards.get(card_data["ItemId"])
            if card is None:
                card = CacheObject(id=card_data["ItemId"], name=card_data["ItemName"])
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
    item : Device | CacheObject
        The purchased item.\n
        `CacheObject` with incomplete cache.
    level : int
        The level of the item purchased.
    """
    def __init__(self, item: Device | CacheObject, level: int):
        self.item: Device | CacheObject = item
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
    cards : list[LoadoutCard]
        A list of loadout cards used.\n
        Will be empty if the player hasn't picked a loadout during the match.
    talent : Device | CacheObject | None
        The talent used.\n
        With incomplete cache, this will be a `CacheObject` with the name and ID set.\n
        `None` when the player hasn't picked a talent during the match.
    passive : Passive | None
        The passive used.
        Currently, this only applies to Octavia, but may affect other champions in the future.
    """
    def __init__(
        self,
        cache_entry: CacheEntry | None,
        match_data: responses.MatchPlayerObject | responses.HistoryMatchObject,
    ):
        if "hasReplay" in match_data:
            # we're in a full match data
            card_key = "Item_Purch_{}"
            talent_key = "Item_Purch_6"
        else:
            # we're in a partial (player history) match data
            card_key = "Item_{}"
            talent_key = "Item_6"
        # cards
        self.cards: list[LoadoutCard] = []
        for i in range(1, 6):  # 1-5
            card_id: int = match_data[f"ItemId{i}"]  # type: ignore[literal-required]
            if not card_id:
                # skip 0s
                continue
            card: Device | CacheObject | None = None
            if cache_entry is not None:
                card = cache_entry.cards.get(card_id)
            if card is None:
                card = CacheObject(
                    id=card_id,
                    name=match_data[card_key.format(i)],  # type: ignore[literal-required]
                )
            self.cards.append(
                LoadoutCard(card, match_data[f"ItemLevel{i}"])  # type: ignore[literal-required]
            )
        self.cards.sort(key=lambda c: c.points, reverse=True)
        # talent
        talent_id: int = match_data["ItemId6"]
        talent: Device | CacheObject | None = None
        if talent_id:
            if cache_entry is not None:
                talent = cache_entry.talents.get(talent_id)
            if talent is None:
                talent = CacheObject(
                    id=talent_id, name=match_data[talent_key]  # type: ignore[literal-required]
                )
        self.talent: Device | CacheObject | None = talent
        # passive
        self.passive: Passive | None = None
        if "hasReplay" in match_data:
            match_data = cast(responses.MatchPlayerObject, match_data)
            if passive_id := match_data["Kills_Phoenix"]:
                self.passive = Passive(passive_id)

    def __repr__(self) -> str:
        if not self.talent:  # pragma: no cover
            # This can happen if the player haven't picked a talent / loadout during the match
            return "No Loadout"
        return f"{self.talent.name}: {'/'.join(str(c.points) for c in self.cards)}"
