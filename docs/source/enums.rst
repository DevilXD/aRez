Enums
=====

Enums represent "named values" one can encounter when working with the API.

All enum members have an alias with the underscores (if present) replaced with spaces.
The only members available via attribute access are the main ones listed
- aliases work only when passing a string into the constructor.
Additionally, it's ensured that all enum members end up without underscores in their names, even
if the attribute they're accessed from has them:

.. code:: py

    class TestEnum(arez.enums.Enum):
        NoSpaces = 0
        Has_Spaces = 1

    >>> TestEnum.NoSpaces
    <TestEnum.NoSpaces: 0>
    >>> TestEnum.Has_Spaces
    <TestEnum.Has_Spaces: 1>
    >>> TestEnum.Has_Spaces.name
    "Has Spaces"

.. warning::

    The enums below use a specialized metaclass to construct the members, different
    from the standard implementation, and fully customized for usage in this wrapper.
    The semantics follow a standard `enum.IntEnum` implementation though, so you know
    what you can expect. Each member has ``name`` and ``value`` attributes, also accessible
    via ``str()`` and ``int()`` usage.

    Trying to construct an enumeration member from incorrect input will result in `None`
    being returned instead of the enumeration member. This allows you to easily handle
    user input validation and conversion, assuming you will expect to get `None` there.
    You can easily test for the matched member with a simple if statement:

    .. code-block:: py

        platform = arez.Platform(user_input)
        if platform is not None:
            # the platform matched and you now have it's memeber stored
            # under the `platform` variable
        else:
            # the platform didn't match any of the known ones

.. currentmodule:: arez.enums

.. autoclass:: Enum
    :members: name, value, __str__, __int__

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
