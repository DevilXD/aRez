<p align="center"><b>An async Python HiRez API wrapper</b></p>

This project was created to simplify access to the API, as well as incorporate some data pre-processing and consistency.
I am aware that [PyRez](https://github.com/luissilva1044894/Pyrez) already exists, however this project aims to do couple of things differently:

- It's entirely async from the ground up, built using 'aiohttp'
- Uses modern objective programming approach
- Utilizes a local data cache to return data-rich objects

This library is supposed to be used as a module. As of right now, only PaladinsAPI is supported, however ther are plans to expand this - please see the section below.

This is an alpha version - everything is a subject to change.
There are plans on expanding the existing framework to incorporate:

1. Main:  
    - [ ] Making PaladinsAPI inherit from BaseAPI  
        - [ ] Support for SmiteAPI (support Smite endpoint URL)  
            - [ ] Support for Teams  
                - [ ] Support for `getteamdetails` endpoint  
                - [ ] Support for `getteamplayers` endpoint  
                - [ ] Support for `searchteams` endpoint  
        - [ ] Support for RealmRoyaleAPI (support Realm Royale endpoint URL)  
    - [ ] Support for Skins (`getgodskins` endpoint)  
    - [ ] Support for `getmatchdetailsbatch` endpoint  
    - [ ] Support for `getqueuestats` endpoint  
    - [ ] Support for `getmatchplayerdetails` endpoint  
2. Optional:  
    - [ ] Support for `getplayeridbyportaluserid` endpoint  
    - [ ] Support for `getplayerachievements` endpoint  
    - [ ] Support for `getmatchidsbyqueue` endpoint