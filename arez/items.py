import re
from typing import Optional, Union, TYPE_CHECKING

from .mixins import APIClient
from .enumerations import DeviceType, Language

if TYPE_CHECKING:
    from .champion import Champion, Ability
    from .player import PartialPlayer, Player  # noqa


class Device:
    """
    Represents a Device - those are usually cards, talents and shop items.

    You can find these on the `CacheEntry.devices` attribute.

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
        The ability this device affects, or a string denoting the affected part of the champion.\n
        Can be `None` in cases where this information couldn't be parsed.
    champion : Optional[Champion]
        The champion this device belongs to.\n
        `None` for shop items.
    base : float
        The base value of the card's or shop item's scaling.\n
        ``0.0`` for talents.
    scale : float
        The scale value of the card's or shop item's scaling.\n
        ``0.0`` for talents.
    cooldown : int
        The cooldown of this device, in seconds.
        ``0`` if there is no cooldown.
    price : int
        The price of this device.
        ``0`` if there's no price (it's free).
    unlocked_at : int
        The champion's mastery level required to unlock this device. Applies only to talents.
        ``0`` means it's unlocked by default.
    """
    _desc_pattern = re.compile(r'\[(.+?)\] (.*)')
    _card_pattern = re.compile(r'{scale=(\d+|0\.\d+)\|(\d+|0\.\d+)}|{(\d+)}')

    def __init__(self, device_data: dict):
        self.description: str = device_data["Description"].strip()
        self.ability: Optional[Union[Ability, str]] = None
        match = self._desc_pattern.match(self.description)
        if match:
            self.ability = match.group(1)
            self.description = match.group(2)
        self.base: float = 0.0
        self.scale: float = 0.0
        match = self._card_pattern.search(self.description)
        if match:
            group3 = match.group(3)
            if group3:
                self.base = float(group3)
                self.scale = float(group3)
            else:
                self.base = float(match.group(1))
                self.scale = float(match.group(2))
        item_type = device_data["item_type"]
        if item_type == "Inventory Vendor - Talents":
            self.type = DeviceType.Talent
        elif (
            item_type.startswith("Card Vendor Rank")
            or item_type == "Inventory Vendor - Champion Cards"
        ):
            self.type = DeviceType.Card
        elif item_type.startswith("Burn Card"):
            self.type = DeviceType.Item
        else:
            self.type = DeviceType.Undefined
        # later overwritten when the device is added to a champion
        self.champion: Optional["Champion"] = None
        self.name: str = device_data["DeviceName"]
        self.id: int = device_data["ItemId"]
        self.icon_url: str = device_data["itemIcon_URL"]
        self.cooldown: int = device_data["recharge_seconds"]
        self.price: int = device_data["Price"]
        self.unlocked_at: int = device_data["talent_reward_level"]

    def __eq__(self, other) -> bool:
        assert isinstance(other, self.__class__)
        return self.id == other.id

    def __repr__(self) -> str:
        return f"{self.type.name}: {self.name}"

    def _attach_champion(self, champion: "Champion"):
        self.champion = champion
        if isinstance(self.ability, str):
            # upgrade the ability string to a full object if possible
            ability = champion.get_ability(self.ability)
            if ability:
                self.ability = ability


class LoadoutCard:
    """
    Represents a Loadout Card.

    Attributes
    ----------
    card : Optional[Device]
        The actual card that belongs to this loadout.\n
        `None` with incomplete cache.
    points : int
        The amount of loadout points that have been assigned to this card.
    """
    def __init__(self, card: Optional[Device], points: int):
        self.card = card
        self.points = points

    def __repr__(self) -> str:
        card_name = self.card.name if self.card else "Unknown"
        return f"{card_name}: {self.points}"


class Loadout(APIClient):
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
    champion : Optional[Champion]
        The champion this loadout belongs to.
        `None` with incomplete cache.
    language : Language
        The language of all the cards this loadout has.
    cards : List[LoadoutCard]
        A list of loadout cards this lodaout consists of.
    """
    def __init__(
        self, player: Union["PartialPlayer", "Player"], language: Language, loadout_data: dict
    ):
        assert player.id == loadout_data["playerId"]
        super().__init__(player._api)
        self.player = player
        self.language = language
        self.champion = self._api.get_champion(loadout_data["ChampionId"], language)
        self.name = loadout_data["DeckName"]
        self.id = loadout_data["DeckId"]
        self.cards = [
            LoadoutCard(self._api.get_card(c["ItemId"], language), c["Points"])
            for c in sorted(loadout_data["LoadoutItems"], key=lambda c: c["Points"], reverse=True)
        ]

    def __repr__(self) -> str:
        champion_name = self.champion.name if self.champion is not None else "Unknown"
        return f"{champion_name}: {self.name}"


class MatchItem:
    """
    Represents an item shop's purchase.

    Attributes
    ----------
    item : Optional[Device]
        The purchased item.\n
        `None` with incomplete cache.
    level : int
        The level of the item purchased.
    """
    def __init__(self, item, level):
        self.item: Optional[Device] = item
        self.level: int = level

    def __repr__(self) -> str:
        item_name = self.item.name if self.item else "Unknown"
        return f"{item_name}: {self.level}"


class MatchLoadout:
    """
    Represents a loadout used in a match.

    Attributes
    ----------
    cards : List[LoadoutCard]
        A list of loadout cards used.\n
        Can be empty if the player haven't picked a loadout during the match.
    talent : Optional[Device]
        The talent used.\n
        `None` when the player haven't picked a talent during the match, or with incomplete cache.
    """
    def __init__(self, api, language: Language, match_data: dict):
        self.cards = []
        for i in range(1, 6):
            card_id = match_data[f"ItemId{i}"]
            if not card_id:
                continue
            self.cards.append(
                LoadoutCard(
                    api.get_card(card_id, language),
                    match_data[f"ItemLevel{i}"]
                )
            )
        self.cards.sort(key=lambda c: c.points, reverse=True)
        self.talent = api.get_talent(match_data["ItemId6"], language)

    def __repr__(self) -> str:
        if self.cards:
            talent_name = self.talent.name if self.talent else "Unknown"
            return f"{talent_name}: {'/'.join(str(c.points) for c in self.cards)}"
        else:
            # This can happen if the player haven't picked a talent / loadout during the match
            return "No Loadout"
