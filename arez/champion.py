from __future__ import annotations

import re
from typing import Any, Optional, Union, List, Dict, Literal, TYPE_CHECKING

from .utils import Lookup
from .enums import AbilityType, DeviceType
from .mixins import CacheClient, CacheObject
from .enums import Language, DeviceType, AbilityType, Rarity

if TYPE_CHECKING:
    from .items import Device
    from .cache import DataCache


__all__ = [
    "Skin",
    "Ability",
    "Champion",
]


def _card_ability_sort(card: Device) -> str:
    ability = card.ability
    if type(ability) == CacheObject:
        return f"z{ability.name}"  # push the card to the very end
    return ability.name


class Ability(CacheObject):
    """
    Represents a Champion's Ability.

    You can find these on the `Champion.abilities` attribute.

    Inherits from `CacheObject`.

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
        self.description: str = self._desc_pattern.sub('\n', desc)
        self.type = AbilityType(ability_data["damageType"], return_default=True)
        self.cooldown: int = ability_data["rechargeSeconds"]
        self.icon_url: str = ability_data["URL"]

    __hash__ = CacheObject.__hash__


class Skin(CacheObject):
    """
    Represents a Champion's Skin and it's information.

    You can get these from the `Champion.get_skins()` method,
    as well as find on various other objects returned from the API.

    Inherits from `CacheObject`.

    Attributes
    ----------
    name : str
        The name of the skin.
    id : int
        The ID of the skin.
    champion : Champion
        The champion this skin belongs to.
    rarity : Rarity
        The skin's rarity.
    """
    def __init__(self, champion: Champion, skin_data: Dict[str, Any]):
        # pre-process champion and skin name
        self.champion: Champion = champion
        skin_name = skin_data["skin_name"]
        if skin_name.endswith(self.champion.name):
            skin_name = skin_name[:-len(self.champion.name)].strip()
        super().__init__(id=skin_data["skin_id2"], name=skin_name)
        rarity: str = skin_data["rarity"]
        self.rarity: Rarity
        if rarity:  # not an empty string
            self.rarity = Rarity(rarity, return_default=True)
        else:
            self.rarity = Rarity.Common

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}: {self._name} {self.champion.name}"
            f"({self.rarity.name}, {self._id})"
        )

class Champion(CacheObject, CacheClient):
    """
    Represents a Champion and it's information.

    You can find these on the `CacheEntry.champions` attribute,
    as well as various other objects returned from the API.

    Inherits from `CacheObject`.

    .. note::

        An object of this class can be `False` in a boolean context, if it's internal state
        is deemed incomplete or corrupted. For the internal state to be considered valid, there has
        to be exactly 16 cards and 3 talents assigned to the champion. If you don't plan on
        accessing / processing those, you can use the ``is not None`` in the check instead.
        Examples:

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

        .. note::

            Some champions may have 7 abilities instead of 5 - this will happen if one of their
            other abilities allows switching the primary and secondary abilities between
            two states.

    talents : Lookup[Device]
        An object that lets you iterate over all talents this champion has.\n
        Use ``list(...)`` to get a list instead.
    cards : Lookup[Device]
        An iterator that lets you iterate over all cards this champion has.\n
        Use ``list(...)`` to get a list instead.
    """
    _name_pattern = re.compile(r'([a-z ]+)(?:/\w+)? \(([a-z ]+)\)', re.I)
    _desc_pattern = re.compile(r'([A-Z][a-zA-Z ]+): ([\w\s\-\'%,.]+)(?:<br><br>|(?:\r|\n)\n|$)')
    _url_pattern = re.compile(r'([a-z\-]+)(?=\.(?:jpg|png))')

    def __init__(
        self,
        cache: DataCache,
        language: Language,
        devices: List[Device],
        champion_data: Dict[str, Any],
    ):
        CacheClient.__init__(self, cache)
        CacheObject.__init__(self, id=champion_data["id"], name=champion_data["Name"])
        self._language = language
        self.title: str = champion_data["Title"]
        self.role: Literal[
            "Front Line", "Support", "Damage", "Flank"
        ] = champion_data["Roles"][9:].replace("er", "")
        self.icon_url: str = champion_data["ChampionIcon_URL"]
        self.lore: str = champion_data["Lore"]
        self.health: int = champion_data["Health"]
        self.speed: int = champion_data["Speed"]

        # Abilities
        abilities = []
        for i in range(1, 6):
            ability_data = champion_data[f"Ability_{i}"]
            # see if this is a composite ability
            match = self._name_pattern.match(ability_data["Summary"])
            if match:
                # yes - we need to split the data into two sets
                composites: Dict[str, Dict[str, Any]] = {}
                name1, name2 = match.groups()
                composites[name1] = {"Summary": name1}
                composites[name2] = {"Summary": name2}
                descs = self._desc_pattern.findall(ability_data["Description"])
                for ability_name, ability_desc in descs:
                    ability_dict = composites.get(ability_name)
                    if ability_dict is None:
                        continue
                    ability_dict["Description"] = ability_desc
                    # modify the URL
                    ability_dict["URL"] = self._url_pattern.sub(
                        ability_name.lower().replace(' ', '-'), ability_data["URL"]
                    )
                    # copy the rest of attributes
                    ability_dict["Id"] = ability_data["Id"]
                    ability_dict["damageType"] = ability_data["damageType"]
                    ability_dict["rechargeSeconds"] = ability_data["rechargeSeconds"]
                    # add the ability
                    abilities.append(Ability(self, ability_dict))
            else:
                # nope - just append it
                abilities.append(Ability(self, ability_data))
        self.abilities: Lookup[Ability] = Lookup(abilities)

        # Talents and Cards
        cards: List[Device] = []
        talents: List[Device] = []
        for d in devices:
            if d.type == DeviceType.Card:
                cards.append(d)
            elif d.type == DeviceType.Talent:  # pragma: no branch
                talents.append(d)
            d._attach_champion(self)  # requires the abilities to exist already
        talents.sort(key=lambda d: d.unlocked_at)
        cards.sort(key=lambda d: d.name)
        cards.sort(key=_card_ability_sort)
        self.cards: Lookup[Device] = Lookup(cards)
        self.talents: Lookup[Device] = Lookup(talents)

    __hash__ = CacheObject.__hash__

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

    def get_card(self, card: Union[str, int], /, *, fuzzy: bool = False) -> Optional[Device]:
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

    def get_talent(self, talent: Union[str, int], /, *, fuzzy: bool = False) -> Optional[Device]:
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

    async def get_skins(self) -> List[Skin]:
        """
        Returns a list of skins this champion has.

        Returns
        -------
        List[Skin]
            The list of skins available.
        """
        response = await self._api.request("getChampionSkins", self.id, self._language.value)
        return sorted((Skin(self, d) for d in response), key=lambda s: s.rarity.value)
