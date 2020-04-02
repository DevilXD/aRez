from __future__ import annotations

import operator
from enum import IntEnum
from functools import partialmethod
from typing import Any, Optional, Union, List, Dict, Tuple, TYPE_CHECKING

__all__ = [
    'Rank',
    'Queue',
    'Region',
    'Activity',
    'Language',
    'Platform',
    'DeviceType',
    'AbilityType',
]


class EnumValue:
    # These get added by the metaclass later
    _default_value: Optional[int]
    _name_mapping: Dict[str, EnumValue]
    _value_mapping: Dict[int, EnumValue]

    # Exists only to stop MyPy from complaining about wrong instance init arguments
    def __init__(self, key_or_value: Optional[Union[str, int]], *, return_default: bool = False):
        # This never runs cos of metaclass
        self._class: type
        self._name: str
        self._value: int

    # The actual factory method
    @classmethod
    def new(cls, name: str, value: int):
        self = super().__new__(cls)
        self._name = name
        self._value = value
        return self

    # Used to support isinstance checks
    def set_class(self, cls: type):
        self._class = cls

    # Enum names are immutable
    @property
    def name(self) -> str:
        return self._name

    # Enum values are immutable
    @property
    def value(self) -> int:
        return self._value

    def __repr__(self) -> str:
        return "<{0.name}: {0.value}>".format(self)

    # Show only the most relevant bits in VSCode
    def __dir__(self) -> List[str]:
        return ["_class", "name", "value"]

    def __str__(self) -> str:
        return self.name

    def __int__(self) -> int:
        return self.value

    # Matches standard enum hashing method
    def __hash__(self) -> int:
        return hash(self._name)

    # Compare using values and optionally the class
    def _cmp(self, opr, other: Union[EnumValue, int]) -> bool:
        try:
            if isinstance(other, int):
                return opr(self._value, other)
            else:
                return self._class is other._class and opr(self._value, other._value)
        except AttributeError:
            return False

    __eq__ = partialmethod(_cmp, operator.eq)  # type: ignore
    __ne__ = partialmethod(_cmp, operator.ne)  # type: ignore
    __lt__ = partialmethod(_cmp, operator.lt)
    __gt__ = partialmethod(_cmp, operator.gt)
    __le__ = partialmethod(_cmp, operator.le)
    __ge__ = partialmethod(_cmp, operator.ge)


# For special methods defined on enums
# def is_descriptor(obj):
#     return hasattr(obj, "__get__")


class EnumMeta(type):
    def __new__(
        meta_cls,
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
        *,
        default_value: Optional[int] = None,
    ):
        new_attrs: Dict[str, Any] = {}

        # Create enum members
        name_mapping: Dict[str, EnumValue] = {}
        value_mapping: Dict[int, EnumValue] = {}
        for k, v in attrs.items():
            # if (k[0] == '_' and k[1] == '_') or is_descriptor(v):
            if k[0] == '_' and k[1] == '_':
                # special attribute or descriptor, pass unchanged
                new_attrs[k] = v
                continue
            if v in value_mapping:
                # existing value, just read it back
                member = value_mapping[v]
            else:
                # create a new value
                # ensure we won't end up with underscores in the name
                member = EnumValue.new(k.replace('_', ' '), v)
                value_mapping[v] = member
                new_attrs[k] = member
            k_lower = k.lower()
            name_mapping[k_lower] = member
            if '_' in k:
                # generate a second alias with spaces instead of underscores
                name_mapping[k_lower.replace('_', ' ')] = member
        new_attrs["_name_mapping"] = name_mapping
        new_attrs["_value_mapping"] = value_mapping
        new_attrs["_default_value"] = default_value

        # Make the new class
        cls = super().__new__(meta_cls, name, bases, new_attrs)
        # Assign to members for future 'isinstance' checks
        for m in value_mapping.values():
            m._class = cls
        return cls

    # Add our special enum member constructor
    def __call__(  # type: ignore
        cls: EnumValue, key_or_value: Optional[Union[str, int]], *, return_default: bool = False
    ) -> Optional[Union[int, str, EnumValue]]:
        if isinstance(key_or_value, str):
            member = cls._name_mapping.get(key_or_value.lower())
        elif isinstance(key_or_value, int):
            member = cls._value_mapping.get(key_or_value)
        else:
            member = None
        if member is not None:
            return member
        if return_default:
            default = cls._default_value
            if default is not None and default in cls._value_mapping:
                # return the default enum value, if defined
                return cls._value_mapping[default]
            return key_or_value  # return the input unchanged
        return None

    # Make 'isinstance' work
    def __instancecheck__(cls, inst):
        try:
            return cls is inst._class
        except AttributeError:
            return False


# Generate additional aliases for ranks
class RankMeta(EnumMeta):
    def __new__(cls, *args, **kwargs):
        roman_numerals = {
            "i": 1,
            "ii": 2,
            "iii": 3,
            "iv": 4,
            "v": 5,
        }
        new_cls: EnumValue = super().__new__(cls, *args, **kwargs)
        more_aliases: Dict[str, EnumValue] = {}
        # generate additional aliases
        for k, v in new_cls._name_mapping.items():
            if ' ' in k or '_' not in k:
                # skip the already-existing aliases with spaces
                # skip members with no underscores in them
                continue
            name, _, level = k.partition('_')
            level_int = roman_numerals[level]  # change the roman number to int
            more_aliases["{}_{}".format(name, level_int)] = v  # roman replaced with integer
            more_aliases["{} {}".format(name, level_int)] = v  # same but with a space
            more_aliases["{}{}".format(name, level_int)] = v  # no delimiter
        # add the aliases
        new_cls._name_mapping.update(more_aliases)
        return new_cls


if TYPE_CHECKING:
    class Enum(EnumValue, IntEnum):  # type: ignore
        pass
else:
    class Enum(EnumValue, metaclass=EnumMeta):
        pass


class Platform(Enum, default_value=0):
    """
    Platform enumeration. Represents player's platform.

    Attributes
    ----------
    Unknown
        Unknown platform. You can sometimes get this when the information either isn't available,
        or the returned value didn't match any of the existing ones.
    PC
        Aliases: ``hirez``, ``standalone``.
    Steam
    PS4
        Aliases: ``psn``, ``playstation``.
    Xbox
        Aliases: ``xb``, ``xboxlive``, ``xbox_live``, ``xboxone``, ``xbox_one``, ``xbox1``,
        ``xbox_1``.
    Switch
        Aliases: ``nintendo_switch``.
    Discord
    Epic_Games
        Aliases: ``epic``.
    """

    Unknown         =  0
    PC              =  1
    HiRez           =  1
    Standalone      =  1
    Steam           =  5
    PS4             =  9
    psn             =  9
    playstation     =  9
    Xbox            = 10
    xb              = 10
    xboxlive        = 10
    xbox_live       = 10
    xboxone         = 10
    xbox_one        = 10
    xbox1           = 10
    xbox_1          = 10
    Mixer           = 14
    Nintendo_Switch = 22
    switch          = 22
    Discord         = 25
    Epic_Games      = 28
    epic            = 28


class Region(Enum, default_value=0):
    """
    Region enumeration. Represents player's region.

    Attributes
    ----------
    Unknown
        Unknown region. You can sometimes get this when the information either isn't available,
        or the returned value didn't match any of the existing ones.
    North_America
        Aliases: ``na``.
    Europe
        Aliases: ``eu``.
    Australia
        Aliases: ``oceania``, ``aus``, ``oce``.
    Brazil
        Aliases: ``br``.
    Latin_America_North
        Aliases: ``latam``.
    Southeast_Asia
        Aliases: ``sea``.
    """

    Unknown             = 0
    North_America       = 1
    na                  = 1
    Europe              = 2
    eu                  = 2
    Australia           = 3
    Oceania             = 3
    aus                 = 3
    oce                 = 3
    Brazil              = 4
    br                  = 4
    Latin_America_North = 5
    latam               = 5
    Southeast_Asia      = 6
    sea                 = 6


class Language(Enum):
    """
    Language enumeration. Represents the response language.

    Attributes
    ----------
    English
        Aliases: ``en``, ``eng``.
    German
        Aliases: ``de``, ``ger``.
    French
        Aliases: ``fr``, ``fre``.
    Chinese
        Aliases: ``zh``, ``chi``.
    Spanish
        Aliases: ``es``, ``spa``.
    Portuguese
        Aliases: ``pt``, ``por``.
    Russian
        Aliases: ``ru``, ``rus``.
    Polish
        Aliases: ``pl``, ``pol``.
    Turkish
        Aliases: ``tr``, ``tur``.
    """

    # Unknown  =  0
    English    =  1
    en         =  1
    eng        =  1
    German     =  2
    de         =  2
    ger        =  2
    French     =  3
    fr         =  3
    fre        =  3
    Chinese    =  5
    zh         =  5
    chi        =  5
    # Spanish  =  7  # old spanish - it seems like this language isn't used that much
    # spanish  =  7  # over the #9 one, and is full of mostly outdated data
    # es       =  7
    Spanish    =  9  # old Latin America
    es         =  9
    spa        =  9
    Portuguese = 10
    pt         = 10
    por        = 10
    Russian    = 11
    ru         = 11
    rus        = 11
    Polish     = 12
    pl         = 12
    pol        = 12
    Turkish    = 13
    tr         = 13
    tur        = 13


class Queue(Enum, default_value=0):
    """
    Queue enumeration. Represents a match queue.

    Attributes
    ----------
    Unknown
        Unknown queue. You can sometimes get this when the information either isn't available,
        or the returned value didn't match any of the existing ones.
    Casual_Siege
        Aliases: ``casual``, ``siege``.
    Team_Deathmatch
        Aliases: ``deathmatch``, ``tdm``.
    Onslaught
    Competitive_Keyboard
        Aliases: ``keyboard_comp``, ``keyboard_ranked``, ``kb_comp``, ``kb_ranked``.
    Competitive_Controller
        Aliases: ``controller_comp``, ``controller_ranked``, ``cn_comp``, ``cn_ranked``.
    Shooting_Range
        Aliases: ``range``.
    Training_Siege
        Aliases: ``bot_siege``.
    Training_Onslaught
        Aliases: ``bot_onslaught``.
    Training_Team_Deathmatch
        Aliases: ``bot_team_deathmatch``, ``bot_deathmatch``, ``bot_tdm``.
    Test_Maps
        Aliases: ``test``.
    """

    Unknown                  =   0
    Casual_Siege             = 424
    casual                   = 424
    siege                    = 424
    Team_Deathmatch          = 469
    deathmatch               = 469
    tdm                      = 469
    Onslaught                = 452
    Competitive_Keyboard     = 486
    keyboard_comp            = 486
    keyboard_ranked          = 486
    kb_comp                  = 486
    kb_ranked                = 486
    Competitive_Controller   = 428
    controller_comp          = 428
    controller_ranked        = 428
    cn_comp                  = 428
    cn_ranked                = 428
    Shooting_Range           = 434
    range                    = 434
    Training_Siege           = 425
    bot_siege                = 425
    Training_Onslaught       = 453
    bot_onslaught            = 453
    Training_Team_Deathmatch = 470
    bot_team_deathmatch      = 470
    bot_deathmatch           = 470
    bot_tdm                  = 470
    Test_Maps                = 445
    test                     = 445


class Rank(EnumValue, metaclass=RankMeta):
    """
    Rank enumeration. Represents player's rank.

    All attributes include an alias consisting of their name and a single digit
    representing the rank's level, alternatively with and without the dividing space existing
    or being replaced with an underscore. For example, all of these will result in the
    'Gold IV' rank: ``gold_iv``, ``gold iv``, ``gold_4``, ``gold4``.

    Attributes
    ----------
    Qualifying
    Bronze_V
    Bronze_IV
    Bronze_III
    Bronze_II
    Bronze_I
    Silver_V
    Silver_IV
    Silver_III
    Silver_II
    Silver_I
    Gold_V
    Gold_IV
    Gold_III
    Gold_II
    Gold_I
    Platinum_V
    Platinum_IV
    Platinum_III
    Platinum_II
    Platinum_I
    Diamond_V
    Diamond_IV
    Diamond_III
    Diamond_II
    Diamond_I
    Master
    Grandmaster
    """

    Qualifying   =  0
    Bronze_V     =  1
    Bronze_IV    =  2
    Bronze_III   =  3
    Bronze_II    =  4
    Bronze_I     =  5
    Silver_V     =  6
    Silver_IV    =  7
    Silver_III   =  8
    Silver_II    =  9
    Silver_I     = 10
    Gold_V       = 11
    Gold_IV      = 12
    Gold_III     = 13
    Gold_II      = 14
    Gold_I       = 15
    Platinum_V   = 16
    Platinum_IV  = 17
    Platinum_III = 18
    Platinum_II  = 19
    Platinum_I   = 20
    Diamond_V    = 21
    Diamond_IV   = 22
    Diamond_III  = 23
    Diamond_II   = 24
    Diamond_I    = 25
    Master       = 26
    Grandmaster  = 27


class DeviceType(Enum, default_value=0):
    """
    DeviceType enumeration. Represents a type of device: talent, card, shop item, etc.

    Attributes
    ----------
    Undefined
        Represents an undefined device type. Devices with this type are usually (often unused)
        talents or cards that couldn't be determined as valid.
    Item
        The device of this type is a Shop Item.
    Card
        The device of this type is a Card.
    Talent
        The device of this type is a Talent.
    """

    Undefined = 0
    Item      = 1
    Card      = 2
    Talent    = 3


class AbilityType(Enum, default_value=0):
    """
    AbilityType enumeration. Represents a type of an ability.

    Currently only damage types are supported.

    Attributes
    ----------
    Undefined
        Represents an undefined ability type. Those abilities often deal no damage,
        or serve another  purpose that doesn't involve them doing so.
    Direct_Damage
        The ability does Direct Damage.
        Aliases: ``direct``.
    Area_Damage
        The ability does Area Damage.
        Aliases: ``aoe``.
    """

    Undefined     = 0
    Direct_Damage = 1
    direct        = 1
    Area_Damage   = 2
    aoe           = 2


class Activity(Enum, default_value=5):
    """
    Activity enumeration. Represents player's in-game status.

    Attributes
    ----------
    Offline
        The player is currently offline.
    In_Lobby
        The player is in the post-match lobby.
    Character_Selection
        The player is currently on the character selection screen before a match.
    In_Match
        The player is currently in a live match.
    Online
        The player is currently online, most likely on the main menu screen.
    Unknown
        The player's status is unknown.
    """

    Offline             = 0
    In_Lobby            = 1
    Character_Selection = 2
    In_Match            = 3
    Online              = 4
    Unknown             = 5
