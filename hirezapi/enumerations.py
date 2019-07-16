from enum import Enum
from typing import Optional

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
    #"Unknown":         0,
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
    "xbox one":         10,
    "xbox1":            10,
    "Switch":           22,
    "switch":           22,
    "nintendo switch":  22,
    "Discord":          25,
    "discord":          25,
})

Region = EnumGet("Region", {
    "Unknown":              0,
    "North America":        1,
    "north america":        1,
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
    "latin america north":  5,
    "latin_america_north":  5,
    "latam":                5,
    "Southeast Asia":       6,
    "southeast asia":       6,
    "sea":                  6,
})

Language = EnumGet("Language", {
    #"Unknown":      0,
    "English":       1,
    "english":       1,
    "German":        2,
    "german":        2,
    "French":        3,
    "french":        3,
    "Chinese":       5,
    "chinese":       5,
    "Spanish":       7,
    "spanish":       7,
    "Latin America": 9,
    "latin_america": 9,
    "Portuguese":    10,
    "portuguese":    10,
    "Russian":       11,
    "russian":       11,
    "Polish":        12,
    "polish":        12,
    "Turkish":       13,
    "turkish":       13,
})

Queue = EnumGet("Queue", {
    #"Unknown":                 0,
    "Casual Siege":             424,
    "casual":                   424,
    "siege":                    424,
    "Team Deathmatch":          469,
    "tdm":                      469,
    "deathmatch":               469,
    "Onslaught":                452,
    "onslaught":                452,
    "Competitive Keyboard":     486,
    "competitive keyboard":     486,
    "keyboard comp":            486,
    "keyboard ranked":          486,
    "kb comp":                  486,
    "kb ranked":                486,
    "Competitive Controller":   428,
    "competitive controller":   428,
    "controller comp":          428,
    "controller ranked":        428,
    "cn comp":                  428,
    "cn ranked":                428,
    "Training Siege":           425,
    "bot siege":                425,
    "Training Onslaught":       453,
    "bot onslaught":            453,
    "Training Team Deathmatch": 470,
    "bot tdm":                  470,
    "bot team deathmatch":      470,
    "Test Maps":                445,
    "test maps":                445,
})

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

DeviceType = EnumGet("DeviceType", {
    "Undefined": 0,
    "Item":      1,
    "Card":      2,
    "Talent":    3,
})

AbilityType = EnumGet("AbilityType", {
    "Undefined":     0,
    "Direct Damage": 1,
    "Direct":        1,
    "Area Damage":   2,
    "AoE":           2,
})

Activity = EnumGet("Activity", {
    "Offline":             0,
    "In Lobby":            1,
    "Character Selection": 2,
    "In Match":            3,
    "Online":              4,
    "Unknown":             5,
})