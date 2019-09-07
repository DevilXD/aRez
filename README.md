## Async Python HiRez API wrapper

This project was created to simplify access to the API, as well as incorporate some data pre-processing and consistency.
I am aware that [PyRez](https://github.com/luissilva1044894/Pyrez) already exists, however this project aims to do couple of things differently:

- It's entirely async from the ground up, built using 'aiohttp'
- Uses modern objective programming approach
- Utilizes a local data cache to return data-rich objects

This library is supposed to be used as a module. **As of right now, only PaladinsAPI is supported.** Smite support is planned - read below.

Currently supported:

- [x] `getgods / getchampions` and `getitems` regarding god / champion and card / talent / shop item information  
- [x] `getplayer` (Player stats)  
- [x] `getplayeridbyname`, `getplayeridsbygamertag` and `searchplayers` under a single, intuitive method (Finding the players)  
- [x] `getfriends` (Player friends)  
- [x] `getgodranks / getchampionranks` (God / Champion stats)  
- [x] `getplayerloadouts` (Player loadouts for each god / champion)  
- [x] `getplayerstatus` (Player status)  
- [x] `getmatchhistory` (Player's recent matches)  
- [x] `getmatchdetails` (Match details, by the ID or from player's recent matches)  
- [x] `getplayeridbyportaluserid` (Finding the player by their Portal ID)  
- [x] `getmatchplayerdetails` (Information about the current player's match)  
- [ ] `getplayerachievements` (Player's achievements)  
- [ ] `getmatchdetailsbatch` (Fetching multiple matches at once)  
- [ ] `getmatchidsbyqueue` (Fetching all matches by queue)  
- [ ] `getqueuestats` (Player match stats by queue)  

There are plans on expanding the existing framework to incorporate the above and below:
 
- [ ] Adding documentation
- [ ] Making PaladinsAPI inherit from BaseAPI  
    - [ ] Support for SmiteAPI (support Smite endpoint URL)  
        - [ ] Support for Teams  
            - [ ] Support for `getteamdetails` endpoint  
            - [ ] Support for `getteamplayers` endpoint  
            - [ ] Support for `searchteams` endpoint  
    - [ ] \(Maybe) Support for RealmRoyaleAPI (support Realm Royale endpoint URL)  

### Requirements

- Python 3.6+ (might work on lower versions too; untested)
- aiohttp 2.0+

### Resources

- [HiRez API documentation](https://docs.google.com/document/d/1OFS-3ocSx-1Rvg4afAnEHlT3917MAK_6eJTR6rzr-BM)

### Usage

Please see [example.py](https://github.com/DevilXD/HiRezAPI/blob/master/example.py) for more examples.

```py
import asyncio
import hirezapi  # import the API

DEV_ID = '1234'  # your Developer ID (example)
AUTH_KEY = 'L2U3M60A03662R24UKOMY0FIT4S2IBKU'  # your Auth Key (example)

async def main():
    api = hirezapi.PaladinsAPI(DEV_ID, AUTH_KEY)  # create an API instance
    player = await api.get_player("DevilXD")  # fetch Player stats
    print(player.ranked_keyboard.rank.name)  # display your rank
    await api.close()  # close the API once you're done with it

loop = asyncio.get_event_loop()
loop.run_until_complete(main())  # run the async loop
```

### Notes

This is an alpha version - as of right now, everything is a subject to change.  
Once both Paladins and Smite (and maybe Realm Royale) APIs are supported, this wrapper is going to have it's v1.0 release, and I will try to manage the versioning the proper way from there.