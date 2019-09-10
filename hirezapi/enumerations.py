from enum import Enum
from typing import Optional

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

class EnumGet(Enum):
    @classmethod
    def get(cls, key_or_value) -> Optional[Enum]:
        if isinstance(key_or_value, str):
            get = cls.__members__.get(key_or_value)
            if not get:
                return cls.__members__.get(key_or_value.lower())
            return get
        elif isinstance(key_or_value, int):
            try:
                return cls(key_or_value)
            except ValueError:
                pass
        return None

Platform = EnumGet("Platform", {
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
    "Xbox":             10,
    "xbox":             10,
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
Platform.__doc__ = "Platform enumeration. Represents player's platform."

Region = EnumGet("Region", {
    "Unknown":              0,
    "unknown":              0,
    "North America":        1,
    "north_america":        1,
    "NA":                   1,
    "na":                   1,
    "Europe":               2,
    "europe":               2,
    "eu":                   2,
    "Oceania":              3,
    "oceania":              3,
    "oce":                  3,
    "Brazil":               4,
    "brazil":               4,
    "Latin America North":  5,
    "latin_america_north":  5,
    "latam":                5,
    "Southeast Asia":       6,
    "southeast_asia":       6,
    "sea":                  6,
})
Region.__doc__ = "Region enumeration. Represents player's region."

Language = EnumGet("Language", {
    #"Unknown":         0,
    "English":          1,
    "english":          1,
    "German":           2,
    "german":           2,
    "French":           3,
    "french":           3,
    "Chinese":          5,
    "chinese":          5,
    "Spanish":          7,
    "spanish":          7,
    "Latin America":    9,
    "latin_america":    9,
    "Portuguese":       10,
    "portuguese":       10,
    "Russian":          11,
    "russian":          11,
    "Polish":           12,
    "polish":           12,
    "Turkish":          13,
    "turkish":          13,
})
Language.__doc__ = "Language enumeration. Represents the response language."

Queue = EnumGet("Queue", {
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
    "Training Siege":           425,
    "bot_siege":                425,
    "Training Onslaught":       453,
    "bot_onslaught":            453,
    "Training Team Deathmatch": 470,
    "bot_team_deathmatch":      470,
    "bot_deathmatch":           470,
    "bot_tdm":                  470,
    "Test Maps":                445,
    "test_maps":                445,
})
Queue.__doc__ = "Queue enumeration. Represents a match queue."

Rank = EnumGet("Rank", {
    "Qualifying":   0,
    "Bronze V":     1,
    "Bronze IV":    2,
    "Bronze III":   3,
    "Bronze II":    4,
    "Bronze I":     5,
    "Silver V":     6,
    "Silver IV":    7,
    "Silver III":   8,
    "Silver II":    9,
    "Silver I":     10,
    "Gold V":       11,
    "Gold IV":      12,
    "Gold III":     13,
    "Gold II":      14,
    "Gold I":       15,
    "Platinum V":   16,
    "Platinum IV":  17,
    "Platinum III": 18,
    "Platinum II":  19,
    "Platinum I":   20,
    "Diamond V":    21,
    "Diamond IV":   22,
    "Diamond III":  23,
    "Diamond II":   24,
    "Diamond I":    25,
    "Master":       26,
    "Grandmaster":  27,
})
Rank.__doc__ = "Rank enumeration. Represents player's rank."

DeviceType = EnumGet("DeviceType", {
    "Undefined":    0,
    "undefined":    0,
    "Item":         1,
    "item":         1,
    "Card":         2,
    "card":         2,
    "Talent":       3,
    "talent":       3,
})
DeviceType.__doc__ = "DeviceType enumeration. Represents a type of device: talent, card, shop item, etc."

AbilityType = EnumGet("AbilityType", {
    "Undefined":        0,
    "Direct Damage":    1,
    "Direct":           1,
    "direct":           1,
    "Area Damage":      2,
    "AoE":              2,
    "aoe":              2,
})
AbilityType.__doc__ = "AbilityType enumeration. Represents a type of an ability."

Activity = EnumGet("Activity", {
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
Activity.__doc__ = "Activity enumeration. Represents player's in-game status."