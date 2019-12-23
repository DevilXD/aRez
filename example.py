import asyncio
from hirezapi import PaladinsAPI, StatusPage

DEV_ID = "1234"  # Your Developer ID (example)
AUTH_KEY = "8HBMWTCWAIZESURZHZND0IRXOZIOLVM5"  # Your Auth Key (example)


async def main():
    ##################################################
    # Paladins API
    ##################################################

    # Standard usage:
    api = PaladinsAPI(DEV_ID, AUTH_KEY)
    player = await api.get_player("DevilXD")  # get player
    status = await player.get_status()  # get their in-game status
    friends = await player.get_friends()  # get their friends list
    loadouts = await player.get_loadouts()  # get their loadouts
    history = await player.get_match_history()  # get their match history
    champ_stats = await player.get_champion_stats()  # get their champion stats
    print(status, friends, loadouts, history, champ_stats, sep='\n')  # print them out
    await api.close()  # don't forget to close when you'll finish using the API

    # Async context manager usage (automatically closes the API for you):
    async with PaladinsAPI(DEV_ID, AUTH_KEY) as api:
        player = await api.get_player("DevilXD")
        print(player)

    ##################################################
    # Status Page
    ##################################################

    # Standard usage:
    api = StatusPage("http://status.hirezstudios.com")
    status = await api.get_status()
    print(status)
    api.close()  # don't forget to close when you'll finish using the API

    # Async context manager usage (automatically closes the API for you):
    async with StatusPage("http://status.hirezstudios.com") as api:
        status = await api.get_status()
        print(status)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
