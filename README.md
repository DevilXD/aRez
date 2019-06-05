## Async Python HiRez API wrapper

This project was created to simplify access to the API, as well as incorporate some data pre-processing and consistency.
I am aware that [PyRez](https://github.com/luissilva1044894/Pyrez) already exists, however this project aims to do couple of things differently:

- It's entirely async from the ground up, built using 'aiohttp'
- Uses modern objective programming approach
- Utilizes a local data cache to return data-rich objects

This library is supposed to be used as a module. **As of right now, only PaladinsAPI is supported.** Smite support is planned - read below.

There are plans on expanding the existing framework to incorporate:
 
- [ ] Adding documentation
- [ ] Creating and making PaladinsAPI inherit from BaseAPI  
    - [ ] Support for SmiteAPI (support Smite endpoint URL)  
        - [ ] Support for Teams  
            - [ ] Support for `getteamdetails` endpoint  
            - [ ] Support for `getteamplayers` endpoint  
            - [ ] Support for `searchteams` endpoint  
    - [ ] \(Maybe) Support for RealmRoyaleAPI (support Realm Royale endpoint URL)  
- [ ] Support for Skins (`getgodskins` endpoint)  
- [ ] Support for `getplayeridbyportaluserid` endpoint  
- [ ] Support for `getmatchplayerdetails` endpoint  
- [ ] Support for `getplayerachievements` endpoint  
- [ ] Support for `getmatchdetailsbatch` endpoint  
- [ ] Support for `getmatchidsbyqueue` endpoint
- [ ] Support for `getqueuestats` endpoint  

### Requirements

- Python 3.6+ (might work on lower versions too; untested)
- Aiohttp 3.5+ (lower versions should be fine as well; untested)

### Resources

- [HiRez API documentation](https://docs.google.com/document/d/1OFS-3ocSx-1Rvg4afAnEHlT3917MAK_6eJTR6rzr-BM)

### Notes

This is an alpha version - as of right now, everything is a subject to change.  
Once both Paladins and Smite (and maybe Realm Royale) APIs are supported, this wrapper is going to have it's v1.0 release, and I will try to manage the versioning the proper way from there.