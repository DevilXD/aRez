Tips and Tricks
===============

API instance management
-----------------------

The library is set to utilize a data cache by default, that allows it to output data-rich objects.
This means that every time you instance the wrapper, the resulting object will have
the cache enabled but empty, and set to fill up with data on the next request that'd require
the cache to be there. Note that filling up the cache takes time and uses a bunch of requests,
so you'll probably want to avoid doing it over and over.

To improve speed and avoid wasting requests, it's recommended to instance the wrapper only once,
and preserve said instance for the entire lifetime of a script or application, closing it
shortly before it's about to finish. If your project is meant to run on a server of sorts,
it's best to save the instance in a global variable, or another variable that'll be easily
accessible by all functions that may need it, and avoid instancing in each method separately.

If you really insist on constant instancing, you may want to consider disabling the cache,
by adding ``cache=False`` keyword argument while instancing, like so:

.. code-block:: py

    DEV_ID: int
    AUTH_KEY: str
    api = arez.PaladinsAPI(DEV_ID, AUTH_KEY, cache=False)


Player searching
----------------

To be able to consistently search for and pinpoint a particular player, you need either
their player ID, or their Name and Platform. The player ID is visible in-game,
on the ``Profile - Overview`` page, in the bottom right corner. The player Name and Platform
are self-explanatory, and should be known to every player.

This example assumes that the player name and platform inputs are provided as strings.
Given two variables: ``player_name`` and ``player_platform``, we can do the following:

.. code-block:: py

    import arez

    # it's assumed you already have a wrapper instance here
    api: arez.PaladinsAPI

    # user inputs
    player_name: str = "Faierie"
    player_platform: str = "pc"

    # convert the input platform to a platform object
    platform = arez.Platform(player_platform)

    # search for the player
    try:
        player_list = await api.search_players(player_name, platform)
    except arez.NotFound:
        print("A player like that couldn't be found!")
        exit()

    # process the returned list - here, for simplicity, we pick the first player returned
    first_player = player_list[0]

    # expand them to get more information
    player = await first_player

    # print their highest rank
    print(player.ranked_best.rank.name)

In this example, we expand the player to print out their rank - normally though,
the `PartialPlayer` object returned can be used to further query information about a particular
player, like their matches history, their status and live match they're currently in,
or champion stats and loadouts they have, etc.
