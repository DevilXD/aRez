from math import floor
from operator import attrgetter
from datetime import datetime, timedelta
from typing import Optional, Union, List, Tuple, Iterable, Generator, AsyncGenerator, overload


def convert_timestamp(timestamp: str) -> Optional[datetime]:
    """
    Converts the timestamp format returned by the API.

    Parameters
    ----------
    timestamp : str
        The string containing the timestamp.

    Returns
    -------
    Optional[datetime]
        A converted datetime object.\n
        `None` is returned if an empty string was passed.
    """
    if timestamp:
        return datetime.strptime(timestamp, "%m/%d/%Y %I:%M:%S %p")
    return None


def get(iterable: Iterable, **attrs):
    """
    Returns the first object from the ``iterable`` which attributes match the
    keyword arguments passed.

    You can use ``__`` to search in nested attributes.

    Parameters
    ----------
    iterable : Iterable
        The iterable to search in.
    **attrs
        The attributes to search for.

    Returns
    -------
    Any
        The first object from the iterable with attributes matching the keyword arguments passed.\n
        `None` is returned if the desired object couldn't be found in the iterable.
    """
    if len(attrs) == 1:  # speed up checks for only one test atribute
        attr, val = attrs.popitem()
        getter = attrgetter(attr.replace('__', '.'))
        for element in iterable:
            if getter(element) == val:
                return element
        return None
    getters = [(attrgetter(attr.replace('__', '.')), val) for attr, val in attrs.items()]
    for element in iterable:
        for getter, val in getters:
            if getter(element) != val:
                break
        else:
            return element
    return None


def get_name_or_id(iterable: Iterable, name_or_id: Union[str, int], *, fuzzy: bool = False):
    """
    A helper function that searches for an object in an iterable based on it's
    ``name`` or ``id`` attributes. The attribute to search with is determined by the
    type of the input (`int` or `str`).

    Parameters
    ----------
    iterable : Iterable
        The iterable to search in.
    name_or_id : Union[str, int]
        The Name or ID of the object you're searching for.
    fuzzy : bool
        When set to `True`, makes the Name search case insensitive.\n
        Defaults to `False`.

    Returns
    -------
    Any
        The first object with matching Name or ID passed.\n
        `None` is returned if such object couldn't be found.
    """
    if isinstance(name_or_id, int):
        return get(iterable, id=name_or_id)
    elif isinstance(name_or_id, str):
        if fuzzy:
            # we have to do it manually here
            name_or_id = name_or_id.lower()
            for e in iterable:
                if e.name.lower() == name_or_id:
                    return e
            return None
        else:
            return get(iterable, name=name_or_id)


def chunk(list_to_chunk: list, chunk_length: int) -> Generator[List, None, None]:
    """
    A helper generator that divides the input list into chunks of ``chunk_length`` length.
    The last chunk may be shorter than specified.

    Parameters
    ----------
    list_to_chunk : list
        The list you want to divide into chunks.
    chunk_length : int
        The length of each chunk.
    """
    for i in range(0, len(list_to_chunk), chunk_length):
        yield list_to_chunk[i:i + chunk_length]


async def expand_partial(iterable: Iterable) -> AsyncGenerator:
    """
    A helper async generator that can be used to automatically expand partial objects for you.
    Any other object found in the ``iterable`` is passed unchanged.

    The following classes are converted:
        `PartialPlayer` -> `Player`\n
        `PartialMatch` -> `Match`

    Parameters
    ----------
    iterable : Iterable
        The iterable containing partial objects.

    Returns
    -------
    AsyncGenerator
        An async generator yielding expanded versions of each partial object.
    """
    from .player import PartialPlayer  # cyclic imports
    from .match import PartialMatch  # cyclic imports
    for element in iterable:
        if isinstance(element, (PartialPlayer, PartialMatch)):
            expanded = await element.expand()
            yield expanded
        else:
            yield element


def _int_divmod(base: Union[int, float], div: Union[int, float]) -> Tuple[int, int]:
    result = divmod(base, div)
    return (int(result[0]), int(result[1]))


class Duration:
    """
    Represents a duration. Allows for easy conversion between time units.

    This object isn't a subclass of `timedelta`, but behaves as such - it's also immutable, and
    anything you'd normally be able to do on a `timedelta` object, should be doable on this
    as well. This includes addition, substraction, multiplication, division (true and floor),
    modulo, divmod, negation and getting absolute value. Operations support the second argument
    being a normal `timedelta`, but the return value is always an instance of this class. If you
    prefer doing math using a normal `timedelta` object, you can use the `to_timedelta` method
    to convert it to such.
    """
    __slots__ = (
        "_days", "_hours", "_minutes", "_seconds", "_microseconds", "_total_seconds"
    )

    def __init__(self, **kwargs):
        self._delta = timedelta(**kwargs)
        self._total_seconds = self._delta.total_seconds()
        self._seconds, self._microseconds = divmod(self._total_seconds, 1)
        self._microseconds = round(self._microseconds * 1e6)  # convert the fractional seconds
        self._minutes, self._seconds = _int_divmod(self._total_seconds, 60)
        self._hours, self._minutes = _int_divmod(self._minutes, 60)
        self._days, self._hours = _int_divmod(self._hours, 24)
        # Typings
        self._microseconds: int
        self._seconds: int
        self._minutes: int
        self._hours: int
        self._days: int

    @property
    def days(self) -> int:
        """
        Returns days as a positive integer.
        """
        return self._days

    @property
    def hours(self) -> int:
        """
        Returns hours in range 0-23.
        """
        return self._hours

    @property
    def minutes(self) -> int:
        """
        Returns minutes in range 0-59.
        """
        return self._minutes

    @property
    def seconds(self) -> int:
        """
        Returns seconds in range of 0-59.
        """
        return self._seconds

    def microseconds(self) -> int:
        """
        Returns microseconds in range 0-999999
        """
        return self._microseconds

    def total_days(self) -> float:
        """
        The total amount of days within the duration, as a `float`.
        """
        return self._total_seconds / 86400

    def total_hours(self) -> float:
        """
        The total amount of hours within the duration, as a `float`.
        """
        return self._total_seconds / 3600

    def total_minutes(self) -> float:
        """
        The total amount of minutes within the duration, as a `float`.
        """
        return self._total_seconds / 60

    def total_seconds(self) -> float:
        """
        The total amount of seconds within the duration, as a `float`.
        """
        return self._total_seconds

    def to_timedelta(self) -> timedelta:
        """
        Converts this `Duration` object into `timedelta`.
        """
        return self._delta

    @classmethod
    def from_timedelta(cls, delta: timedelta) -> "Duration":
        """
        Returns a `Duration` instance constructed from a `timedelta` object.
        """
        return cls(seconds=delta.total_seconds())

    def __repr__(self) -> str:
        args = []
        if self._days:
            args.append(("days", self._days))
        if self._hours or self._minutes or self._seconds:
            args.append(("seconds", self._hours * 3600 + self._minutes * 60 + self._seconds))
        if self._microseconds:
            args.append(("microseconds", self._microseconds))
        return "Duration({})".format(", ".join("{}={}".format(*a) for a in args))

    def __str__(self) -> str:
        if self._days:
            s = 's' if abs(self._days) > 1 else ''
            days = "{} day{}, ".format(self._days, s)
        else:
            days = ''
        if self._hours:
            hours = "{}:".format(self._hours)
        else:
            hours = ''
        if self._microseconds:
            ms = ".{:06}".format(self._microseconds)
        else:
            ms = ''
        return "{}{}{:02}:{:02}{}".format(days, hours, self._minutes, self._seconds, ms)

    def _get_delta(self, other) -> timedelta:
        if isinstance(other, type(self)):
            return other._delta
        elif isinstance(other, timedelta):
            return other
        else:
            return NotImplemented

    def __add__(self, other: Union["Duration", timedelta]) -> "Duration":
        delta = self._get_delta(other)
        return Duration(seconds=self._total_seconds + delta.total_seconds())

    __radd__ = __add__

    def __sub__(self, other: Union["Duration", timedelta]) -> "Duration":
        delta = self._get_delta(other)
        return Duration(seconds=self._total_seconds - delta.total_seconds())

    def __rsub__(self, other: Union["Duration", timedelta]) -> "Duration":
        delta = self._get_delta(other)
        return Duration(seconds=delta.total_seconds() - self._total_seconds)

    def __mul__(self, other: Union[int, float]) -> "Duration":
        if not isinstance(other, (int, float)):
            return NotImplemented
        return Duration(seconds=self._total_seconds * other)

    __rmul__ = __mul__

    @overload
    def __truediv__(self, other: Union["Duration", timedelta]) -> float:
        ...

    @overload
    def __truediv__(self, other: Union[int, float]) -> "Duration":
        ...

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Duration(seconds=self._total_seconds / other)
        delta = self._get_delta(other)
        return self._total_seconds / delta.total_seconds()

    def __rtruediv__(self, other: timedelta) -> float:
        if not isinstance(other, timedelta):
            return NotImplemented
        return other.total_seconds() / self._total_seconds

    @overload
    def __floordiv__(self, other: Union["Duration", timedelta]) -> int:
        ...

    @overload
    def __floordiv__(self, other: int) -> "Duration":
        ...

    def __floordiv__(self, other):
        if isinstance(other, int):
            return Duration(microseconds=floor(self._total_seconds * 1e6 // other))
        delta = self._get_delta(other)
        return int(self._total_seconds // delta.total_seconds())

    def __rfloordiv__(self, other: timedelta) -> int:
        if not isinstance(other, timedelta):
            return NotImplemented
        return int(other.total_seconds() // self._total_seconds)

    def __mod__(self, other: Union["Duration", timedelta]) -> "Duration":
        delta = self._get_delta(other)
        return Duration(seconds=(self._total_seconds % delta.total_seconds()))

    def __rmod__(self, other: Union["Duration", timedelta]) -> "Duration":
        delta = self._get_delta(other)
        return Duration(seconds=(delta.total_seconds() % self._total_seconds))

    def __divmod__(self, other: Union["Duration", timedelta]) -> Tuple[int, "Duration"]:
        delta = self._get_delta(other)
        q, r = divmod(self._total_seconds, delta.total_seconds())
        return (int(q), Duration(seconds=r))

    def __rdivmod__(self, other: timedelta) -> Tuple[int, "Duration"]:
        q, r = divmod(other.total_seconds(), self._total_seconds)
        return (int(q), Duration(seconds=r))

    def __pos__(self):
        return Duration(seconds=self._total_seconds)

    def __neg__(self):
        return Duration(seconds=-self._total_seconds)

    def __abs__(self):
        if self._total_seconds < 0:
            return Duration(seconds=-self._total_seconds)
        return Duration(seconds=self._total_seconds)
