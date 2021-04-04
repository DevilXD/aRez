from __future__ import annotations

from typing import Optional, List, TypedDict, Literal, SupportsInt


class IntStr(SupportsInt, str):
    pass


class RetMsg(TypedDict):
    ret_msg: Optional[str]


class SessionObject(TypedDict):
    ret_msg: str  # this is always populated, with either "Approved" or an error
    session_id: str  # empty string means the session wasn't approved
    timestamp: str


class PatchInfoObject(RetMsg):
    version_string: str


class ServerStatusObject(RetMsg):
    entry_datetime: Optional[str]
    environment: Literal["live", "pts"]
    limited_access: bool
    platform: Literal["pc", "ps4", "xbox", "switch"]
    status: Literal["UP", "DOWN"]
    version: Optional[str]


class MergedPlayerObject(RetMsg):
    merge_datetime: str
    playerId: IntStr
    portalId: IntStr


class RankedStatsObject(RetMsg):
    Leaves: int
    Losses: int
    Name: Literal["Conquest", "Ranked Controller", "Ranked KBM"]
    Points: int
    PrevRank: int
    Rank: int
    Season: int
    Tier: int
    Trend: int
    Wins: int
    player_id: None


class PlayerObject(RetMsg):
    ActivePlayerId: int
    AvatarId: int
    AvatarURL: Optional[str]
    Created_Datetime: str
    HoursPlayed: int
    Id: int
    Last_Login_Datetime: str
    Leaves: int
    Level: int
    LoadingFrame: Optional[str]
    Losses: int
    MasteryLevel: int
    MergedPlayers: Optional[List[MergedPlayerObject]]
    MinutesPlayed: int
    Name: str
    Personal_Status_Message: Literal['']
    Platform: str
    RankedConquest: RankedStatsObject  # empty for Paladins
    RankedController: RankedStatsObject
    RankedKBM: RankedStatsObject
    Region: str
    TeamId: Literal[0]
    Team_Name: Literal['']
    Tier_Conquest: Literal[0]
    Tier_RankedController: int
    Tier_RankedKBM: int
    Title: Optional[str]
    Total_Achievements: int
    Total_Worshippers: int
    Total_XP: int
    Wins: int
    hz_gamer_tag: Optional[str]
    hz_player_name: Optional[str]


class AbilityObject(RetMsg):
    Description: str
    Id: int
    Summary: str  # ability name
    URL: str
    damageType: Literal["Direct", "AoE", "Physical", "True"]  # physical and true don't matter
    rechargeSeconds: int


class ChampionObject(RetMsg):
    Ability1: str
    Ability2: str
    Ability3: str
    Ability4: str
    Ability5: str
    AbilityId1: int
    AbilityId2: int
    AbilityId3: int
    AbilityId4: int
    AbilityId5: int
    Ability_1: AbilityObject
    Ability_2: AbilityObject
    Ability_3: AbilityObject
    Ability_4: AbilityObject
    Ability_5: AbilityObject
    ChampionAbility1_URL: str
    ChampionAbility2_URL: str
    ChampionAbility3_URL: str
    ChampionAbility4_URL: str
    ChampionAbility5_URL: str
    ChampionCard_URL: Literal['']
    ChampionIcon_URL: str
    Cons: Literal['']
    Health: int
    Lore: str
    Name: str
    Name_English: str
    OnFreeRotation: Literal['']
    OnFreeWeeklyRotation: Literal['', "true"]  # empty string means no / false
    Pantheon: Literal['', "Norse"]
    Pros: Literal['']
    Roles: Literal[
        "Paladins Front Line", "Paladins Support", "Paladins Damage", "Paladins Flanker"
    ]
    Speed: int
    Title: str
    Type: Literal['']
    abilityDescription1: str
    abilityDescription2: str
    abilityDescription3: str
    abilityDescription4: str
    abilityDescription5: str
    id: int
    latestChampion: Literal['y', 'n']


class DeviceObject(RetMsg):
    Description: str
    DeviceName: str
    IconId: int
    ItemId: int
    Price: int
    ShortDesc: str
    champion_id: int  # 0 if there's no champion assigned
    itemIcon_URL: str
    item_type: Literal[
        "Burn Card Defense Vendor",
        "Burn Card Utility Vendor",
        "Burn Card Healing Vendor",
        "Burn Card Damage Vendor",
        "Card Vendor Rank 1 Epic",
        "Card Vendor Rank 1 Rare",
        "Inventory Vendor - Champion Cards",
        "Inventory Vendor - Talents",
        "Inventory Vendor - Talents Default",
        "zDeprecated Card Vendor Rank 4",
    ]
    recharge_seconds: int  # cooldown of the card or talent
    talent_reward_level: int  # non-zero only for talents


class ChampionSkinObject(RetMsg):
    champion_id: int
    champion_name: str
    rarity: Literal['', "Common", "Uncommon", "Rare", "Epic", "Legendary", "Unlimited", "Limited"]
    skin_id1: int
    skin_id2: int
    skin_name: str
    skin_name_english: str


class MatchPlayerObject(RetMsg):
    Account_Level: int
    ActiveId1: int
    ActiveId2: int
    ActiveId3: int
    ActiveId4: int
    ActiveLevel1: Literal[0, 1, 2]
    ActiveLevel2: Literal[0, 1, 2]
    ActiveLevel3: Literal[0, 1, 2]
    ActiveLevel4: Literal[0, 1, 2]
    ActivePlayerId: IntStr
    Assists: int
    BanId1: int
    BanId2: int
    BanId3: int
    BanId4: int
    Ban_1: Optional[str]
    Ban_2: Optional[str]
    Ban_3: Optional[str]
    Ban_4: Optional[str]
    Camps_Cleared: Literal[0]
    ChampionId: int
    Damage_Bot: Literal[0]
    Damage_Done_In_Hand: int
    Damage_Done_Magical: Literal[0]
    Damage_Done_Physical: int
    Damage_Mitigated: int
    Damage_Player: int
    Damage_Taken: int
    Damage_Taken_Magical: Literal[0]
    Damage_Taken_Physical: int
    Deaths: int
    Distance_Traveled: Literal[0]
    Entry_Datetime: str
    Final_Match_Level: Literal[0]
    Gold_Earned: int
    Gold_Per_Minute: int
    Healing: int
    Healing_Bot: Literal[0]
    Healing_Player_Self: int
    ItemId1: int
    ItemId2: int
    ItemId3: int
    ItemId4: int
    ItemId5: int
    ItemId6: int
    ItemLevel1: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel2: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel3: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel4: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel5: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel6: Literal[0]
    Item_Active_1: str
    Item_Active_2: str
    Item_Active_3: str
    Item_Active_4: str
    Item_Purch_1: str
    Item_Purch_2: str
    Item_Purch_3: str
    Item_Purch_4: str
    Item_Purch_5: str
    Item_Purch_6: str
    Killing_Spree: int
    Kills_Bot: int
    Kills_Double: Literal[0]
    Kills_Fire_Giant: int  # siege payload push successes
    Kills_First_Blood: Literal[0]
    Kills_Gold_Fury: int  # siege points captured
    Kills_Penta: Literal[0]
    Kills_Phoenix: Literal[0]
    Kills_Player: int
    Kills_Quadra: Literal[0]
    Kills_Siege_Juggernaut: Literal[0]
    Kills_Single: Literal[0]
    Kills_Triple: Literal[0]
    # https://podio.com/hirezstudioscom/smite-api-developer-collaboration/status/11737890
    Kills_Wild_Juggernaut: int  # unused, explanation in the above link
    League_Losses: int  # these 4 are filled / non-zero only for ranked matches
    League_Points: int
    League_Tier: int
    League_Wins: int
    Map_Game: str  # map name
    Mastery_Level: int
    Match: int  # match ID
    Match_Duration: int  # in seconds, unused
    MergedPlayers: Optional[List[MergedPlayerObject]]
    Minutes: int
    Multi_kill_Max: int
    Objective_Assists: int
    PartyId: int
    Platform: str
    Rank_Stat_League: Literal[0]
    Reference_Name: str  # champion name
    Region: str
    Skin: str  # skin name
    SkinId: int
    Structure_Damage: Literal[0]
    Surrendered: Literal[0]
    TaskForce: Literal[1, 2]
    Team1Score: int
    Team2Score: int
    TeamId: Literal[0]
    Team_Name: Literal['']
    Time_In_Match_Seconds: int
    Towers_Destroyed: Literal[0]
    Wards_Placed: Literal[0]
    Win_Status: Literal["Winner", "Loser"]
    Winning_TaskForce: Literal[1, 2]
    hasReplay: Literal["y", "n"]
    hz_gamer_tag: Optional[str]
    hz_player_name: Optional[str]
    match_queue_id: int
    name: str  # queue name
    playerId: IntStr
    playerName: str
    playerPortalId: IntStr
    playerPortalUserId: IntStr


class PlayerStatusObject(RetMsg):
    Match: int
    match_queue_id: int
    personal_status_message: None
    status: int
    status_string: str


class LivePlayerObject(RetMsg):
    Account_Champions_Played: int
    Account_Level: int
    ChampionId: int
    ChampionLevel: int
    ChampionName: str
    Mastery_Level: int
    Match: int
    Queue: IntStr  # queue ID
    Skin: str  # skin name
    SkinId: int
    Tier: int  # player's rank, non-zero only for ranked matches
    mapGame: str  # map name
    playerCreated: str  # date
    playerId: IntStr
    playerName: str
    playerPortalId: IntStr
    playerPortalUserId: IntStr
    playerRegion: str
    taskForce: Literal[1, 2]
    tierLosses: int  # non-zero only for ranked matches
    tierWins: int  # non-zero only for ranked matches


class HistoryMatchObject(RetMsg):
    ActiveId1: int
    ActiveId2: int
    ActiveId3: int
    ActiveId4: int
    ActiveLevel1: Literal[0, 4, 8]
    ActiveLevel2: Literal[0, 4, 8]
    ActiveLevel3: Literal[0, 4, 8]
    ActiveLevel4: Literal[0, 4, 8]
    Active_1: str
    Active_2: str
    Active_3: str
    Active_4: str
    Assists: int
    Champion: str  # champion name
    ChampionId: int
    Creeps: Literal[0]
    Damage: int
    Damage_Bot: Literal[0]
    Damage_Done_In_Hand: int
    Damage_Mitigated: int
    Damage_Structure: Literal[0]
    Damage_Taken: int
    Damage_Taken_Magical: Literal[0]
    Damage_Taken_Physical: int
    Deaths: int
    Distance_Traveled: Literal[0]
    Gold: int
    Healing: int
    Healing_Bot: Literal[0]
    Healing_Player_Self: int
    ItemId1: int
    ItemId2: int
    ItemId3: int
    ItemId4: int
    ItemId5: int
    ItemId6: int
    ItemLevel1: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel2: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel3: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel4: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel5: Literal[0, 1, 2, 3, 4, 5]
    ItemLevel6: Literal[0]
    Item_1: str
    Item_2: str
    Item_3: str
    Item_4: str
    Item_5: str
    Item_6: str
    Killing_Spree: int
    Kills: int
    Level: Literal[0]
    Map_Game: str  # map name
    Match: int
    Match_Queue_Id: int
    Match_Time: str  # timestamp
    Minutes: int
    Multi_kill_Max: int
    Objective_Assists: int
    Queue: str  # queue name
    Region: str
    Skin: str  # skin name
    SkinId: int
    Surrendered: Literal[0]
    TaskForce: Literal[1, 2]
    Team1Score: int
    Team2Score: int
    Time_In_Match_Seconds: int
    Wards_Placed: Literal[0]
    Win_Status: Literal["Win", "Loss"]
    Winning_TaskForce: Literal[1, 2]
    playerId: int
    playerName: str


class PartialPlayerObject(RetMsg):
    Name: str
    player_id: int
    portal: str
    portal_id: IntStr
    privacy_flag: Literal['y', 'n']


class PlayerSearchObject(PartialPlayerObject):
    hz_player_name: str


class MatchSearchObject(RetMsg):
    Active_Flag: Literal['y', 'n']
    Entry_Datetime: str  # timestamp
    Match: IntStr


class BountyItemObject(RetMsg):
    active: Literal['y', 'n']
    bounty_item_id1: int
    bounty_item_id2: int
    bounty_item_name: str
    champion_id: int
    champion_name: str
    final_price: IntStr
    initial_price: IntStr
    sale_end_datetime: str  # timestamp
    sale_type: Literal["Increasing", "Decreasing"]


class PlayerFriendObject(RetMsg):
    account_id: IntStr
    friend_flags: IntStr
    name: str
    player_id: IntStr
    portal_id: IntStr
    status: str


class LoadoutItemObject(TypedDict):
    ItemId: int
    ItemName: str
    Points: Literal[1, 2, 3, 4, 5]


class ChampionLoadoutObject(RetMsg):
    ChampionId: int
    ChampionName: str
    DeckId: int
    DeckName: str
    LoadoutItems: List[LoadoutItemObject]
    playerId: int
    playerName: str


class ChampionRankObject(RetMsg):
    Assists: int
    Deaths: int
    Gold: int
    Kills: int
    LastPlayed: str  # timestamp
    Losses: int
    MinionKills: int
    Minutes: int
    Rank: int
    Wins: int
    Worshippers: int
    champion: str
    champion_id: IntStr
    player_id: IntStr


class ChampionQueueRankObject(RetMsg):
    Assists: int
    Champion: str
    ChampionId: int
    Deaths: int
    Gold: int  # credits
    Kills: int
    LastPlayed: str  # timestamp
    Losses: int
    Matches: int
    Minutes: int
    Queue: Literal['']
    Wins: int
    player_id: IntStr
