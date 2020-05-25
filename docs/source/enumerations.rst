Enumerations
============

Enumerations represent "named values" one can encounter when working with the API.

All enumeration members have a lowercase alias equivalent, with the underscores (if present)
replaced with spaces. The only members available via attribute access are the main ones listed
- aliases work only when passing a string into the constructor.

.. note::

    These enumerations use a specialized metaclass to construct the members, different
    from the standard implementation, and fully customized for usage in this wrapper.
    The semantics roughly follow a standard `enum.IntEnum` implementation though, so you know
    what you can expect. Each member has ``name`` and ``value`` attributes, also accessible
    via ``str()`` and ``int()`` usage. The ``return_default`` kwarg is reserved for internal
    usage and thus is a subject to change without warnings - do not rely on it.

.. warning::

    If ``return_default`` is set to `False` (the default), trying to construct an enumeration
    member from incorrect input will return you `None` instead of the enumeration member.
    This allows you to easily handle user input validation and conversion, assuming you will
    expect to get `None` there. You can easily test for the matched member with a simple
    if statement:

    .. code-block:: py

        platform = arez.Platform(user_input)
        if platform is not None:
            # the platform matched and you now have it's memeber stored
            # under the `platform` variable
        else:
            # the platform didn't match any of the known ones

.. currentmodule:: arez

.. autoclass:: Platform
    :members:

.. autoclass:: Rank
    :members:

.. autoclass:: Queue
    :members:

.. autoclass:: Region
    :members:

.. autoclass:: Language
    :members:

.. autoclass:: DeviceType
    :members:

.. autoclass:: Activity
    :members:

.. autoclass:: AbilityType
    :members:
