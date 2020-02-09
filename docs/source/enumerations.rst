Enumerations
============

Enumerations represent "named values" one can encounter when working with the API.

All enumerations are a subclass of an ``EnumGet`` class, that adds a single utility method
described below.

All enumeration members have a lowercase alias equivalent, with the spaces (if present) replaced
with underscores - this is for attribute access and ease of use purposes only.
Example: ``Latin America`` -> ``latin_america``

.. currentmodule:: arez.enumerations

.. automethod:: EnumGet.get

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
