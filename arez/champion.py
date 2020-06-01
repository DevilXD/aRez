from __future__ import annotations

import re
from typing import Any, Optional, Union, List, Dict, Literal, TYPE_CHECKING

from .utils import Lookup
from .mixins import CacheObject
from .enumerations import DeviceType, AbilityType

if TYPE_CHECKING:  # pragma: no branch
    from .items import Device


__all__ = [
    "Ability",
    "Champion",
]


def _card_ability_sort(card: Device) -> str:
    ability = card.ability
    if ability is None:
        return "zz"  # push the card to the very, very end
    elif type(ability) == CacheObject:
        return f"z{ability.name}"  # push the card to the very end
    return ability.name


class Ability(CacheObject):
    """
    Represents a Champion's Ability.
    You can find these on the `Champion.abilities` attribute.

    Attributes
    ----------
    name : str
        The name of the ability.
    id : int
        The ID of the ability.
    champion : Champion
        The champion this ability belongs to.
    description : str
        The description of the ability.
    type : AbilityType
        The type of the ability (currently only damage type).
    cooldown : int
        The ability's cooldown, in seconds.
    icon_url : str
        A URL of this ability's icon.
    """
    _desc_pattern = re.compile(r" ?<br>(?:<br>)? ?")  # replace the <br> tags with a new line

    def __init__(self, champion: Champion, ability_data: Dict[str, Any]):
        super().__init__(id=ability_data["Id"], name=ability_data["Summary"])
        self.champion = champion
        desc = ability_data["Description"].strip().replace('\r', '')
        desc = self._desc_pattern.sub('\n', desc)
        self.description: str = desc
        self.type = AbilityType(ability_data["damageType"], return_default=True)
        self.cooldown: int = ability_data["rechargeSeconds"]
        self.icon_url: str = ability_data["URL"]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}({self.id})"


class Champion(CacheObject):
    """
    Represents a Champion and it's information.
    You can find these on the `CacheEntry.champions` attribute, as well as various other objects
    returned from the API.

    An object of this class can be `False` in a boolean context, if it's internal state
    is deemed incomplete or corrupted. For the internal state to be considered valid, there has
    to be exactly 16 cards and 3 talents assigned to the champion. If you don't plan on accessing /
    processing those, you can use the ``is not None`` in the check instead. Examples:

    .. code-block:: py

        if champion:
            # champion exists and is valid
        if not champion:
            # champion doesn't exist, or exists in an invalid state
        if champion is not None:
            # champion exists but might be invalid
        if champion is None:
            # champion doesn't exist

    Attributes
    ----------
    name : str
        The name of the champion.
    id : int
        The ID of the champion.
    title : str
        The champion's title.
    role : Literal["Front Line", "Support", "Damage", "Flank"]
        The champion's role.
    lore : str
        The champion's lore.
    icon_url : str
        A URL of this champion's icon.
    health : int
        The amount of health points this champion has at base.
    speed : int
        The champion's speed.
    abilities : Lookup[Ability]
        An object that lets you iterate over all abilities this champion has.\n
        Use ``list(...)`` to get a list instead.
    talents : Lookup[Device]
        An object that lets you iterate over all talents this champion has.\n
        Use ``list(...)`` to get a list instead.
    cards : Lookup[Device]
        An iterator that lets you iterate over all cards this champion has.\n
        Use ``list(...)`` to get a list instead.
    """
    def __init__(self, devices: List[Device], champion_data: Dict[str, Any]):
        super().__init__(id=champion_data["id"], name=champion_data["Name"])
        self.title: str = champion_data["Title"]
        self.role: Literal[
            "Front Line", "Support", "Damage", "Flank"
        ] = champion_data["Roles"][9:].replace("er", "")
        self.icon_url: str = champion_data["ChampionIcon_URL"]
        self.lore: str = champion_data["Lore"]
        self.health: int = champion_data["Health"]
        self.speed: int = champion_data["Speed"]

        # Abilities
        self.abilities: Lookup[Ability] = Lookup(
            Ability(self, champion_data[f"Ability_{i}"])
            for i in range(1, 6)
        )

        # Talents and Cards
        talents: List[Device] = []
        cards: List[Device] = []
        for d in devices:
            if d.type == DeviceType.Card:
                cards.append(d)
            elif d.type == DeviceType.Talent:  # pragma: no branch
                talents.append(d)
            d._attach_champion(self)
        talents.sort(key=lambda d: d.unlocked_at)
        cards.sort(key=lambda d: d.name)
        cards.sort(key=_card_ability_sort)
        self.talents: Lookup[Device] = Lookup(talents)
        self.cards: Lookup[Device] = Lookup(cards)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self.id == other.id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}({self.id})"

    def __bool__(self) -> bool:
        return len(self.cards) == 16 and len(self.talents) == 3

    def get_ability(
        self, ability: Union[str, int], /, *, fuzzy: bool = False
    ) -> Optional[Ability]:
        """
        Returns an ability for this champion with the given Name or ID.

        Parameters
        ----------
        ability : Union[str, int]
            The ability's Name or ID you want to get.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Ability]
            The ability you requested.\n
            `None` is returned if the ability couldn't be found.
        """
        return self.abilities._lookup(ability, fuzzy=fuzzy)

    def get_card(self, card: Union[str, int], /, *, fuzzy: bool = False) -> Optional["Device"]:
        """
        Returns a card for this champion with the given Name or ID.

        Parameters
        ----------
        card : Union[str, int]
            The card's Name or ID you want to get.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The card you requested.\n
            `None` is returned if the card couldn't be found.
        """
        return self.cards._lookup(card, fuzzy=fuzzy)

    def get_talent(self, talent: Union[str, int], /, *, fuzzy: bool = False) -> Optional["Device"]:
        """
        Returns a talent for this champion with the given Name or ID.

        Parameters
        ----------
        talent : Union[str, int]
            The talent's Name or ID you want to get.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[Device]
            The talent you requested.\n
            `None` is returned if the talent couldn't be found.
        """
        return self.talents._lookup(talent, fuzzy=fuzzy)
