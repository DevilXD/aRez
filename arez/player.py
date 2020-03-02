from typing import Optional, Union, List, SupportsInt, TYPE_CHECKING

from .items import Loadout
from .exceptions import Private
from .match import PartialMatch
from .status import PlayerStatus
from .mixins import APIClient, Expandable
from .utils import convert_timestamp, Duration
from .enumerations import Language, Platform, Region
from .stats import Stats, RankedStats, ChampionStats

if TYPE_CHECKING:
    from .api import PaladinsAPI  # noqa


class PartialPlayer(APIClient, Expandable):
    """
    This object stores basic information about a player, such as their Player ID, Player Name
    and their Platform. Depending on the way it was created, only the Player ID is guaranteed
    to exist - both ``name`` and ``platform`` can be an empty string and `Platform.Unknown`
    respectively.

    To ensure all attributes are filled up correctly before processing, you can upgrade this
    object to `Player` by awaiting on it and using the result:

    .. code-block:: py

        player = await partial_player
    """
    def __init__(
        self,
        api: "PaladinsAPI",
        *,
        id: SupportsInt,
        name: str = '',
        platform: Union[str, int] = 0,
        private: bool = False,
    ):
        super().__init__(api)
        self._id = int(id)
        self._name = str(name)
        if isinstance(platform, str) and platform.isdecimal():
            platform = int(platform)
        self._platform = Platform.get(platform) or Platform(0)
        self._private = bool(private)

    async def _expand(self) -> Optional["Player"]:
        """
        Expands and refreshes the information stored inside this object.

        Uses up a single request.

        Returns
        -------
        Optional[Player]
            A full player object with all fields filled up, for the same player.\n
            `None` is returned if this player could not be found.

        Raises
        ------
        Private
            The player's profile was private.
        """
        if self.private:
            raise Private
        player_list = await self._api.request("getplayer", self._id)
        if not player_list:
            return None
        player_data = player_list[0]
        if player_data["ret_msg"]:
            raise Private
        return Player(self._api, player_data)

    def __eq__(self, other) -> bool:
        assert isinstance(other, self.__class__)
        return self._id != 0 and other.id != 0 and self._id == other.id

    def __repr__(self):
        platform = self.platform.name if self.platform else None
        return "{0.__class__.__name__}: {0.name}({0.id} / {1})".format(self, platform)

    @property
    def id(self) -> int:
        """
        ID of the player. A value of ``0`` indicates a private player account, and shouldn't be
        used to distinguish between different players.

        :type: int
        """
        return self._id

    @property
    def name(self) -> str:
        """
        Name of the player.

        :type: str
        """
        return self._name

    @property
    def platform(self) -> Platform:
        """
        The player's platform.

        :type: Platform
        """
        return self._platform

    @property
    def private(self) -> bool:
        """
        Checks to see if this profile is private or not.

        Trying to fetch any information for a private profile will raise the `Private` exception.

        Returns
        -------
        bool
            `True` if this player profile is considered private, `False` otherwise.
        """
        return self._private or self._id == 0

    async def get_status(self) -> Optional[PlayerStatus]:
        """
        Fetches the player's current status.

        Uses up a single request.

        Returns
        -------
        Optional[PlayerStatus]
            The player's status.\n
            `None` is returned if this player could not be found.

        Raises
        ------
        Private
            The player's profile was private.
        """
        if self.private:
            raise Private
        response = await self._api.request("getplayerstatus", self._id)
        if response and response[0]["status"] != 5:
            return PlayerStatus(self, response[0])
        return None

    async def get_friends(self) -> List["PartialPlayer"]:
        """
        Fetches the player's friend list.

        Uses up a single request.

        Returns
        -------
        List[PartialPlayer]
            A list of players this player is friends with.

        Raises
        ------
        Private
            The player's profile was private.
        """
        if self.private:
            raise Private
        response = await self._api.request("getfriends", self._id)
        return [
            PartialPlayer(self._api, id=p["player_id"], name=p["name"])
            for p in response
            if p["status"] == "Friend"
        ]

    async def get_loadouts(self, language: Optional[Language] = None) -> List[Loadout]:
        """
        Fetches the player's loadouts.

        Uses up a single request.

        Parameters
        ----------
        language : Optional[Language]
            The `Language` you want to fetch the information in.
            Default language is used if not provided.

        Returns
        -------
        List[Loadout]
            A list of player's loadouts.

        Raises
        ------
        Private
            The player's profile was private.
        """
        assert language is None or isinstance(language, Language)
        if self.private:
            raise Private
        if language is None:
            language = self._api._default_language
        # ensure we have champion information first
        await self._api.get_champion_info(language)
        response = await self._api.request("getplayerloadouts", self._id, language.value)
        if not response or response and not response[0]["playerId"]:
            return []
        return [Loadout(self, language, l) for l in response]

    async def get_champion_stats(
        self, language: Optional[Language] = None
    ) -> List[ChampionStats]:
        """
        Fetches the player's champion statistics.

        Uses up a single request.

        Parameters
        ----------
        language : Optional[Language]
            The `Language` you want to fetch the information in.
            Default language is used if not provided.

        Returns
        -------
        List[ChampionStats]
            A list of champion statistics objects, one for each played champion.

        Raises
        ------
        Private
            The player's profile was private.
        """
        assert language is None or isinstance(language, Language)
        if self.private:
            raise Private
        if language is None:
            language = self._api._default_language
        # ensure we have champion information first
        await self._api.get_champion_info(language)
        response = await self._api.request("getgodranks", self._id)
        return [ChampionStats(self, language, s) for s in response]

    async def get_match_history(self, language: Optional[Language] = None) -> List[PartialMatch]:
        """
        Fetches player's match history.

        Uses up a single request.

        Parameters
        ----------
        language : Optional[Language]
            The `Language` you want to fetch the information in.
            Default language is used if not provided.

        Returns
        -------
        List[PartialMatch]
            A list of partial matches, containing statistics for the current player only.

        Raises
        ------
        Private
            The player's profile was private.
        """
        assert language is None or isinstance(language, Language)
        if self.private:
            raise Private
        if language is None:
            language = self._api._default_language
        # ensure we have champion information first
        await self._api.get_champion_info(language)
        response = await self._api.request("getmatchhistory", self._id)
        if not response or response and response[0]["ret_msg"]:
            return []
        return [PartialMatch(self, language, m) for m in response]


class Player(PartialPlayer):
    """
    A full Player object, containing all the information about a player.

    This inherits from `PartialPlayer`, so all it's methods should be present here as well.

    Attributes
    ----------
    platform_name : str
        The platform name of this profile. This is usually identical to `name`, except in cases
        where the platform allows nicknames (Steam profiles).
    active_player : Optional[PartialPlayer]
        The current active player between merged profiles.\n
        `None` if the current profile is the active profile.
    merged_players : List[PartialPlayer]
        A list of all merged profiles.
    created_at : datetime.datetime
        A timestamp of the profile's creation date.
    last_login : datetime.datetime
        A timestamp of the profile's last successful in-game login.
    level : int
        The in-game level of this profile.
    playtime : Duration
        The amount of time spent playing on this profile.
    champion_count : int
        The amount of champions this player unlocked.
    region : Region
        The player's currently set Region.
    total_achievements : int
        The amount of achievements the player has.
    total_experience : int
        The total amount of experience the player has.
    casual : Stats
        Player's casual statistics.
    ranked_keyboard : RankedStats
        Player's ranked keyboard statistics.
    ranked_controller : RankedStats
        Player's ranked controller statistics.
    """
    def __init__(self, api: "PaladinsAPI", player_data):
        player_name = player_data["hz_player_name"]
        gamer_tag = player_data["hz_gamer_tag"]
        name: str = player_data["Name"]
        self.platform_name: str = name
        if player_name:
            name = player_name
        elif gamer_tag:
            name = gamer_tag
        super().__init__(
            api,
            id=player_data["Id"],
            name=name,
            platform=player_data["Platform"],
            # No private kwarg here, since this object can only exist for non-private accounts
        )
        self.active_player: Optional[PartialPlayer] = None
        if player_data["ActivePlayerId"] != self._id:
            self.active_player = PartialPlayer(api, id=player_data["ActivePlayerId"])
        self.merged_players: List[PartialPlayer] = []
        if player_data["MergedPlayers"]:
            for p in player_data["MergedPlayers"]:
                self.merged_players.append(
                    PartialPlayer(api, id=p["playerId"], platform=p["portalId"])
                )
        self.created_at = convert_timestamp(player_data["Created_Datetime"])
        self.last_login = convert_timestamp(player_data["Last_Login_Datetime"])
        self.level: int = player_data["Level"]
        self.playtime = Duration(hours=player_data["HoursPlayed"])
        self.champion_count: int = player_data["MasteryLevel"]
        self.region = Region.get(player_data["Region"]) or Region(0)
        self.total_achievements: int = player_data["Total_Achievements"]
        self.total_experience: int = player_data["Total_Worshippers"]
        self.casual = Stats(player_data)
        self.ranked_keyboard = RankedStats("Keyboard", player_data["RankedKBM"])
        self.ranked_controller = RankedStats("Controller", player_data["RankedController"])

    @property
    def ranked_best(self) -> RankedStats:
        """
        Returns the ranked stats with the highest rank, between the keyboard and controller ones.

        If the rank is the same, winrate is used to determine the one returned.

        :type: RankedStats
        """
        if self.ranked_controller.rank == self.ranked_keyboard.rank:
            return max(self.ranked_keyboard, self.ranked_controller, key=lambda r: r.winrate)
        return max(self.ranked_keyboard, self.ranked_controller, key=lambda r: r.rank)
