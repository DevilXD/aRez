from enum import IntEnum
from contextlib import suppress
from typing import Optional, Union

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


class EnumGet(IntEnum):
    @classmethod
    def get(cls, key_or_value: Union[str, int]) -> Optional["EnumGet"]:
        """
        Allows for exception-less and case-insensitive enumeration member aquisition.

        Parameters
        ----------
        key_or_value : Union[str, int]
            A string or value representing the member you want to get.

        Returns
        -------
        Optional[EnumGet]
            The matched enumeration memeber.\n
            `None` is returned if one couldn't be matched.
        """
        if isinstance(key_or_value, str):
            get = cls.__members__.get(key_or_value)
            if not get:
                key_or_value = key_or_value.lower().replace(' ', '_')
                get = cls.__members__.get(key_or_value)
            return get
        elif isinstance(key_or_value, int):
            with suppress(ValueError):
                return cls(key_or_value)
        return None


Platform = EnumGet("Platform", {  # type: ignore
    "Unknown":          0,
    "unknown":          0,
    "PC":               1,
    "pc":               1,
    "HiRez":            1,
    "hirez":            1,
    "Steam":            5,
    "steam":            5,
    "PS4":              9,
    "ps4":              9,
    "psn":              9,
    "playstation":      9,
    "Xbox":             10,
    "xbox":             10,
    "xb":               10,
    "xboxlive":         10,
    "xboxone":          10,
    "xbox_one":         10,
    "xbox1":            10,
    "Mixer":            14,
    "mixer":            14,
    "Switch":           22,
    "switch":           22,
    "nintendo_switch":  22,
    "Discord":          25,
    "discord":          25,
})
Platform.__doc__ = """
Platform enumeration. Represents player's platform.

Attributes
----------
Unknown
    Unknown platform. You can sometimes get this when the information either isn't available,
    or the returned value didn't match any of the existing ones.
PC
HiRez
    Equivalent to `PC`.
Steam
PS4
    Aliases: ``psn``, ``playstation``
Xbox
    Aliases: ``xb``, ``xboxlive``, ``xboxone``, ``xbox_one``, ``xbox1``
Switch
    Aliases: ``nintendo switch``, ``nintendo_switch``
Discord
"""

Region = EnumGet("Region", {  # type: ignore
    "Unknown":              0,
    "unknown":              0,
    "North America":        1,
    "north_america":        1,
    "na":                   1,
    "Europe":               2,
    "europe":               2,
    "eu":                   2,
    "Australia":            3,
    "Oceania":              3,
    "australia":            3,
    "oceania":              3,
    "aus":                  3,
    "oce":                  3,
    "Brazil":               4,
    "brazil":               4,
    "br":                   4,
    "Latin America North":  5,
    "latin_america_north":  5,
    "latam":                5,
    "Southeast Asia":       6,
    "southeast_asia":       6,
    "sea":                  6,
})
Region.__doc__ = """
Region enumeration. Represents player's region.

Attributes
----------
Unknown
    Unknown region. You can sometimes get this when the information either isn't available,
    or the returned value didn't match any of the existing ones.
North America
    Aliases: ``na``
Europe
    Aliases: ``eu``
Australia
    Also known as Oceania.
    Aliases: ``aus``, ``oce``
Brazil
    Aliases: ``br``
Latin America North
    Aliases: ``latam``
Southeast Asia
    Aliases: ``sea``
"""

Language = EnumGet("Language", {  # type: ignore
    # "Unknown":        0,
    "English":          1,
    "english":          1,
    "en":               1,
    "eng":              1,
    "German":           2,
    "german":           2,
    "de":               2,
    "ger":              2,
    "French":           3,
    "french":           3,
    "fr":               3,
    "fre":              3,
    "Chinese":          5,
    "chinese":          5,
    "zh":               5,
    "chi":              5,
    # "Spanish":        7,  # old spanish - it seems like this language isn't used that much
    # "spanish":        7,  # over the #9 one, and is full of mostly outdated data
    # "es":             7,
    "Spanish":          9,  # old Latin America
    "spanish":          9,  # old latin_america
    "es":               9,  # old Latin America
    "spa":              9,
    "Portuguese":       10,
    "portuguese":       10,
    "pt":               10,
    "por":              10,
    "Russian":          11,
    "russian":          11,
    "ru":               11,
    "rus":              11,
    "Polish":           12,
    "polish":           12,
    "pl":               12,
    "pol":              12,
    "Turkish":          13,
    "turkish":          13,
    "tr":               13,
    "tur":              13,
})
Language.__doc__ = """
Language enumeration. Represents the response language.

Attributes
----------
English
    Aliases: ``en``, ``eng``
German
    Aliases: ``de``, ``ger``
French
    Aliases: ``fr``, ``fre``
Chinese
    Aliases: ``zh``, ``chi``
Spanish
    Aliases: ``es``, ``spa``
Portuguese
    Aliases: ``pt``, ``por``
Russian
    Aliases: ``ru``, ``rus``
Polish
    Aliases: ``pl``, ``pol``
Turkish
    Aliases: ``tr``, ``tur``
"""

Queue = EnumGet("Queue", {  # type: ignore
    "Unknown":                  0,
    "unknown":                  0,
    "Casual Siege":             424,
    "casual_siege":             424,
    "casual":                   424,
    "siege":                    424,
    "Team Deathmatch":          469,
    "team_deathmatch":          469,
    "deathmatch":               469,
    "tdm":                      469,
    "Onslaught":                452,
    "onslaught":                452,
    "Competitive Keyboard":     486,
    "competitive_keyboard":     486,
    "keyboard_comp":            486,
    "keyboard_ranked":          486,
    "kb_comp":                  486,
    "kb_ranked":                486,
    "Competitive Controller":   428,
    "competitive_controller":   428,
    "controller_comp":          428,
    "controller_ranked":        428,
    "cn_comp":                  428,
    "cn_ranked":                428,
    "Shooting Range":           434,
    "shooting_range":           434,
    "range":                    434,
    "Training Siege":           425,
    "training_siege":           425,
    "bot_siege":                425,
    "Training Onslaught":       453,
    "training_onslaught":       453,
    "bot_onslaught":            453,
    "Training Team Deathmatch": 470,
    "training_team_deathmatch": 470,
    "bot_team_deathmatch":      470,
    "bot_deathmatch":           470,
    "bot_tdm":                  470,
    "Test Maps":                445,
    "test_maps":                445,
    "test":                     445,
})
Queue.__doc__ = """
Queue enumeration. Represents a match queue.

Attributes
----------
Unknown
    Unknown queue. You can sometimes get this when the information either isn't available,
    or the returned value didn't match any of the existing ones.
Casual Siege
    Aliases: ``casual``, ``siege``
Team Deathmatch
    Aliases: ``deathmatch``, ``tdm``
Onslaught
Competitive Keyboard
    Aliases: ``keyboard_comp``, ``keyboard_ranked``, ``kb_comp``, ``kb_ranked``
Competitive Controller
    Aliases: ``controller_comp``, ``controller_ranked``, ``cn_comp``, ``cn_ranked``
Shooting Range
    Aliases: ``range``
Training Siege
    Aliases: ``bot_siege``
Training Onslaught
    Aliases: ``bot_onslaught``
Training Team Deathmatch
    Aliases: ``bot_team_deathmatch``, ``bot_deathmatch``, ``bot_tdm``
Test Maps
    Aliases: ``test``
"""

Rank = EnumGet("Rank", {  # type: ignore
    "Qualifying":   0,
    "qualifying":   0,
    "Bronze V":     1,
    "bronze_5":     1,
    "Bronze IV":    2,
    "bronze_4":     2,
    "Bronze III":   3,
    "bronze_3":     3,
    "Bronze II":    4,
    "bronze_2":     4,
    "Bronze I":     5,
    "bronze_1":     5,
    "Silver V":     6,
    "silver_5":     6,
    "Silver IV":    7,
    "silver_4":     7,
    "Silver III":   8,
    "silver_3":     8,
    "Silver II":    9,
    "silver_2":     9,
    "Silver I":     10,
    "silver_1":     10,
    "Gold V":       11,
    "gold_5":       11,
    "Gold IV":      12,
    "gold_4":       12,
    "Gold III":     13,
    "gold_3":       13,
    "Gold II":      14,
    "gold_2":       14,
    "Gold I":       15,
    "gold_1":       15,
    "Platinum V":   16,
    "platinum_5":   16,
    "Platinum IV":  17,
    "platinum_4":   17,
    "Platinum III": 18,
    "platinum_3":   18,
    "Platinum II":  19,
    "platinum_2":   19,
    "Platinum I":   20,
    "platinum_1":   20,
    "Diamond V":    21,
    "diamond_5":    21,
    "Diamond IV":   22,
    "diamond_4":    22,
    "Diamond III":  23,
    "diamond_3":    23,
    "Diamond II":   24,
    "diamond_2":    24,
    "Diamond I":    25,
    "diamond_1":    25,
    "Master":       26,
    "master":       26,
    "Grandmaster":  27,
    "grandmaster":  27,
})
Rank.__doc__ = """
Rank enumeration. Represents player's rank.

All attributes include an alias consisting of their lowercase name, an underscore, and a single
digit representing the rank's level. Example: ``gold_4``.

Attributes
----------
Qualifying
Bronze V
Bronze IV
Bronze III
Bronze II
Bronze I
Silver V
Silver IV
Silver III
Silver II
Silver I
Gold V
Gold IV
Gold III
Gold II
Gold I
Platinum V
Platinum IV
Platinum III
Platinum II
Platinum I
Diamond V
Diamond IV
Diamond III
Diamond II
Diamond I
Master
Grandmaster
"""

DeviceType = EnumGet("DeviceType", {  # type: ignore
    "Undefined":    0,
    "undefined":    0,
    "Item":         1,
    "item":         1,
    "Card":         2,
    "card":         2,
    "Talent":       3,
    "talent":       3,
})
DeviceType.__doc__ = """
DeviceType enumeration. Represents a type of device: talent, card, shop item, etc.

Attributes
----------
Undefined
    Represents an undefined device type. Devices with this type are usually (often unused) talents
    or cards that couldn't be determined as valid.
Item
    The device of this type is a Shop Item.
Card
    The device of this type is a Card.
Talent
    The device of this type is a Talent.
"""

AbilityType = EnumGet("AbilityType", {  # type: ignore
    "Undefined":        0,
    "Direct Damage":    1,
    "direct_damage":    1,
    "direct":           1,
    "Area Damage":      2,
    "area_damage":      2,
    "aoe":              2,
})
AbilityType.__doc__ = """
AbilityType enumeration. Represents a type of an ability.

Currently only damage types are supported.

Attributes
----------
Undefined
    Represents an undefined ability type. Those abilities often deal no damage, or serve another
    purpose that doesn't involve them doing so.
Direct Damage
    The ability does Direct Damage. Aliases: ``direct``
Area Damage
    The ability does Area Damage. Aliases: ``aoe``
"""

Activity = EnumGet("Activity", {  # type: ignore
    "Offline":              0,
    "offline":              0,
    "In Lobby":             1,
    "in_lobby":             1,
    "Character Selection":  2,
    "character_selection":  2,
    "In Match":             3,
    "in_match":             3,
    "Online":               4,
    "online":               4,
    "Unknown":              5,
    "unknown":              5,
})
Activity.__doc__ = """
Activity enumeration. Represents player's in-game status.

Attributes
----------
Offline
    The player is currently offline.
In Lobby
    The player is in the post-match lobby.
Character Selection
    The player is currently on the character selection screen before a match.
In Match
    The player is currently in a live match.
Online
    The player is currently online, most likely on the main menu screen.
Unknown
    The player's status is unknown.
"""
