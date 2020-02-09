from typing import Optional, Union, List, Literal, Iterator, TYPE_CHECKING

from .utils import Lookup
from .enumerations import DeviceType, AbilityType

if TYPE_CHECKING:
    from .items import Device


def _card_ability_sort(card: "Device"):
    if card.ability is None or isinstance(card.ability, str):
        return "z{}".format(card.ability)  # push the card to the very end
    return card.ability.name


class Ability:
    """
    Represents a Champion's Ability.

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
    def __init__(self, champion: "Champion", ability_data: dict):
        self.name: str = ability_data["Summary"]
        self.id: int = ability_data["Id"]
        self.champion = champion
        self.description: str = ability_data["Description"].strip().replace('\r', '')
        self.type = AbilityType.get(ability_data["damageType"]) or AbilityType(0)
        self.cooldown: int = ability_data["rechargeSeconds"]
        self.icon_url: str = ability_data["URL"]

    def __repr__(self) -> str:
        return "{0.__class__.__name__}: {0.name}({0.id})".format(self)


class Champion:
    """
    Represents a Champion.

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
    """
    def __init__(self, devices: List["Device"], champion_data: dict):
        self.name: str = champion_data["Name"]
        self.id: int = champion_data["id"]
        self.title: str = champion_data["Title"]
        self.role: Literal[
            "Front Line", "Support", "Damage", "Flank"
        ] = champion_data["Roles"][9:].replace("er", "")
        self.icon_url: str = champion_data["ChampionIcon_URL"]
        self.lore: str = champion_data["Lore"]
        self.health: int = champion_data["Health"]
        self.speed: int = champion_data["Speed"]

        # Abilities
        self._abilities: Lookup[Ability] = Lookup(
            Ability(self, champion_data["Ability_{}".format(i)])
            for i in range(1, 6)
        )

        # Talents and Cards
        talents: List["Device"] = []
        cards: List["Device"] = []
        for d in devices:
            if d.type == DeviceType["Undefined"]:
                continue
            elif d.type == DeviceType["Card"]:
                cards.append(d)
            elif d.type == DeviceType["Talent"]:
                talents.append(d)
            d._attach_champion(self)
        talents.sort(key=lambda d: d.unlocked_at)
        cards.sort(key=lambda d: d.name)
        cards.sort(key=_card_ability_sort)
        self._talents: Lookup["Device"] = Lookup(talents)
        self._cards: Lookup["Device"] = Lookup(cards)

    def __eq__(self, other) -> bool:
        assert isinstance(other, self.__class__)
        return self.id == other.id

    def __repr__(self) -> str:
        return "{0.__class__.__name__}: {0.name}({0.id})".format(self)

    def __bool__(self) -> bool:
        return len(self._cards) == 16 and len(self._talents) == 3

    @property
    def abilities(self) -> Iterator[Ability]:
        """
        An iterator that lets you iterate over all abilities this champion has.

        Use ``list()`` to get a list instead.
        """
        return iter(self._abilities)

    @property
    def talents(self) -> Iterator["Device"]:
        """
        An iterator that lets you iterate over all talents this champion has.

        Use ``list()`` to get a list instead.
        """
        return iter(self._talents)

    @property
    def cards(self) -> Iterator["Device"]:
        """
        An iterator that lets you iterate over all cards this champion has.

        Use ``list()`` to get a list instead.
        """
        return iter(self._cards)

    def get_ability(self, ability: Union[str, int], *, fuzzy: bool = False) -> Optional[Ability]:
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
        return self._abilities.lookup(ability, fuzzy=fuzzy)

    def get_card(self, card: Union[str, int], *, fuzzy: bool = False) -> Optional["Device"]:
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
        return self._cards.lookup(card, fuzzy=fuzzy)

    def get_talent(self, talent: Union[str, int], *, fuzzy: bool = False) -> Optional["Device"]:
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
        return self._talents.lookup(talent, fuzzy=fuzzy)
