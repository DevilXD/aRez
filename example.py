import asyncio
from hirezapi import PaladinsAPI, StatusPage

DEV_ID = "1234"
DEV_KEY = "8HBMWTCWAIZESURZHZND0IRXOZIOLVM5"

async def main():
    async with PaladinsAPI(DEV_ID, DEV_KEY) as api:
        player = await api.get_player("DevilXD")
        status = await player.get_status()
        friends = await player.get_friends()
        loadouts = await player.get_loadouts()
        history = await player.get_match_history()
        champ_stats = await player.get_champion_stats()
        print(status,friends,loadouts,history,champ_stats,sep='\n')
    async with StatusPage("http://status.hirezstudios.com") as api:
        status = await api.get_status()
        print(status)
    
loop = asyncio.get_event_loop()
loop.run_until_complete(main())