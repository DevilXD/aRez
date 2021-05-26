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

    Trying to construct an enum member from incorrect input will result in `None`
    being returned instead of the enum member. This allows you to easily handle
    user input validation and conversion, checking for `None` in the assigned variable.
    You can easily test for the matched member with a simple if statement:

    .. code-block:: py

        user_input: str
        platform = arez.Platform(user_input)
        if platform is None:
            print("Incorrect platform!")
        else:
            # the platform matched and you now have it stored under the `platform` variable

.. currentmodule:: arez.enums

.. autoclass:: Enum(name_or_value)
    :members: name, value, __str__, __int__

.. currentmodule:: arez

.. autoclass:: Platform(name_or_value)
    :members:

.. autoclass:: Rank(name_or_value)
    :members:

.. autoclass:: Queue(name_or_value)
    :members:

.. autoclass:: Rarity(name_or_value)
    :members:

.. autoclass:: Region(name_or_value)
    :members:

.. autoclass:: Language(name_or_value)
    :members:

.. autoclass:: DeviceType(name_or_value)
    :members:

.. autoclass:: Activity(name_or_value)
    :members:

.. autoclass:: AbilityType(name_or_value)
    :members:
