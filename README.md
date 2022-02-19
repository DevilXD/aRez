## Async Python HiRez API wrapper

This project was created to simplify access to the API, as well as incorporate some data
pre-processing and consistency. I am aware that [PyRez](https://github.com/luissilva1044894/Pyrez)
already exists, however this project aims to do couple of things differently:

- It's entirely async from the ground up, built using 'aiohttp'
- Uses modern objective programming approach
- Utilizes a local data cache to return data-rich objects

This library is supposed to be used as a module.
**As of right now, only PaladinsAPI is supported.** Smite support is planned - please read below.

Currently supported:

- [x] `getgods / getchampions` and `getitems` regarding god / champion
and card / talent / shop item information
- [x] `getplayer` (Player stats)
- [x] `getplayerbatch` (Multiple player stats at once)
- [x] `getplayeridbyname`, `getplayeridsbygamertag` and `searchplayers` under a single,
intuitive method (Finding the players)
- [x] `getfriends` (Player friends)
- [x] `getgodranks / getchampionranks` (God / Champion stats)
- [x] `getplayerloadouts` (Player loadouts for each god / champion)
- [x] `getplayerstatus` (Player status)
- [x] `getmatchhistory` (Player's recent matches)
- [x] `getmatchdetails` (Match details, by the ID or from player's recent matches)
- [x] `getplayeridbyportaluserid` (Finding the player by their Portal ID)
- [x] `getmatchplayerdetails` (Information about the current player's match)
- [ ] `getplayerachievements` (Player overall match stats)
- [x] `getmatchdetailsbatch` (Fetching multiple matches at once)
- [x] `getmatchidsbyqueue` (Fetching all matches by queue)
- [x] `getqueuestats` (Player match stats by queue)

There are plans on expanding the existing framework to incorporate the above and below:

- [x] Adding documentation
- [ ] Support for SmiteAPI (support Smite endpoint URL)
    - [ ] Support for Teams
        - [ ] Support for `getteamdetails` endpoint
        - [ ] Support for `getteamplayers` endpoint
        - [ ] Support for `searchteams` endpoint

If you have some experience with Smite and it's API, and would be interested in working with me
together on expanding this project, please don't hessitate to contact me
(you can find contact information below).

### Requirements

- Python 3.8+
- aiohttp 2.0+

### Resources

- [aRez Documentation](https://arez.readthedocs.io/en/latest/)
- [Official HiRez API Documentation](
    https://docs.google.com/document/d/1OFS-3ocSx-1Rvg4afAnEHlT3917MAK_6eJTR6rzr-BM
)

### Usage

Please see [example.py](https://github.com/DevilXD/aRez/blob/master/example.py) for more examples.

```py
import asyncio

import arez  # import the wrapper

DEV_ID = 1234  # your Developer ID (example)
AUTH_KEY = "L2U3M60A03662R24UKOMY0FIT4S2IBKU"  # your Auth Key (example)

async def main():
    # create an API instance
    api = arez.PaladinsAPI(DEV_ID, AUTH_KEY)
    # fetch Player stats
    player = await api.get_player(5959045)
    # display your rank
    print(player.ranked_best.rank.name)
    # close the API once you're done with it
    await api.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())  # run the async loop
```

### Support

<div align="center">

[![Buy me a coffee](https://i.imgur.com/cL95gzE.png)](
    https://www.buymeacoffee.com/DevilXD
)
[![Support me on Patreon](https://i.imgur.com/Mdkb9jq.png)](
    https://www.patreon.com/bePatron?u=26937862
)

</div>

### Contact

Reddit: https://www.reddit.com/u/DevilXD

Discord: `DevilXD#4437`

### Notes

This is an alpha version - as of right now, everything is a subject to change.
Once both Paladins and Smite (and maybe Realm Royale) APIs are supported, this wrapper is going to
have it's v1.0 release, and I will try to manage the versioning the proper way from there.
