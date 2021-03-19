import arez
import asyncio


DEV_ID = 1234  # Your Developer ID (example)
AUTH_KEY = "8HBMWTCWAIZESURZHZND0IRXOZIOLVM5"  # Your Auth Key (example)


async def main():
    ##################################################
    # Paladins API
    ##################################################

    # create an API instance - normally you need to create this only when starting up your
    # application, so I recommend storing it in an easily accessible place somewhere
    api = arez.PaladinsAPI(DEV_ID, AUTH_KEY)

    # get a PC player directly by their name, or any player by their Player ID
    player = await api.get_player("Player")
    player = await api.get_player(5959045)
    # check if a player like that exists
    if not player:
        # handle this here
        raise RuntimeError

    # OR

    # get an instance of Platform
    # this is safe for user input, and supports multiple different aliases
    platform = arez.Platform("xbox")
    # check if the user input matched any platform
    if not platform:
        # handle this here
        raise RuntimeError
    # search for a player on that platform
    player_list = await api.search_players("Redbana", platform)
    # check if any player got returned
    if not player_list:
        # handle this here
        raise RuntimeError
    # iterate over the player list and pick a player you're the most interested in
    # here we pick the first one returned for simplicity
    partial_player = player_list[0]

    # get their in-game status
    player_status = await partial_player.get_status()
    # get the match they're currently in
    live_match = await player_status.get_live_match()
    # get their friends list
    friends = await partial_player.get_friends()
    # get their loadouts
    loadouts = await partial_player.get_loadouts()
    # get their match history
    history = await partial_player.get_match_history()
    # get their champion stats
    champ_stats = await partial_player.get_champion_stats()

    # print them out (or process as necessary)
    print(player_status, live_match, friends, loadouts, history, champ_stats, sep='\n')

    # don't forget to close the API when you'll finish using it - this needs to be called
    # just before application exit, to properly clean up the resources used and prevent warnings.
    await api.close()

    # Async context manager usage (automatically closes the API for you):
    async with arez.PaladinsAPI(DEV_ID, AUTH_KEY) as api:
        player = await api.get_player("DevilXD")
        print(player)

    ##################################################
    # Status Page
    ##################################################

    # Standard usage:
    status_page = arez.StatusPage("http://status.hirezstudios.com")
    status = await status_page.get_status()
    print(status)
    await status_page.close()  # don't forget to close when you'll finish using the API

    # Async context manager usage (automatically closes the API for you):
    async with arez.StatusPage("http://status.hirezstudios.com") as status_page:
        status = await status_page.get_status()
        print(status)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
