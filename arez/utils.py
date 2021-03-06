from __future__ import annotations

from math import floor
from functools import partialmethod
from weakref import WeakValueDictionary
from datetime import datetime, timedelta
from operator import attrgetter, eq, ne, lt, le, gt, ge
from typing import (
    Optional,
    Union,
    Any,
    List,
    Dict,
    Tuple,
    Mapping,
    Callable,
    Iterable,
    Iterator,
    Generator,
    AsyncGenerator,
    TypeVar,
    cast,
    overload,
)

from .mixins import CacheObject


__all__ = [
    # functions
    "get",
    "chunk",
    "expand_partial",
    # classes
    "Lookup",
    "Duration",
    "WeakValueDefaultDict",
]
# Type variable for internal utils typing
X = TypeVar("X")
Y = TypeVar("Y")


LookupType = TypeVar("LookupType", bound=CacheObject)


def _convert_timestamp(timestamp: str) -> Optional[datetime]:
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


def _convert_map_name(map_name: str) -> str:
    """
    Converts the map name, removing the unneeded prefixes.

    Parameters
    ----------
    map_name : str
        The string representing the map name.

    Returns
    -------
    str
        The converted map name.
    """
    map_name = map_name.strip()
    for prefix in ("LIVE ", "Ranked ", "Practice ", "WIP "):
        if map_name.startswith(prefix):
            map_name = map_name[len(prefix):]
    for suffix in (" (Siege)", " (Onslaught)", " (TDM)", " (KOTH)"):
        if map_name.endswith(suffix):
            map_name = map_name[:-len(suffix)]
    return map_name


# Generates API-valid series of date and hour parameters for the 'getmatchidsbyqueue' endpoint
def _date_gen(
    start: datetime, end: datetime, *, reverse: bool = False
) -> Generator[Tuple[str, str], None, None]:
    # normalize and floor start and end to 10 minutes step resolution
    start = start.replace(minute=(
        start.minute // 10 * 10
    ), second=0, microsecond=0)
    end = end.replace(minute=(
        end.minute // 10 * 10
    ), second=0, microsecond=0)
    # check if the time slice is too short - save on processing by quitting early
    if start >= end:
        return
    # helpful time intervals
    one_day = timedelta(days=1)
    one_hour = timedelta(hours=1)
    ten_minutes = timedelta(minutes=10)

    if reverse:
        if end.minute > 0:
            # round down end to the nearest hour
            closest_hour = end.replace(minute=0)
            while end > closest_hour:
                end -= ten_minutes
                yield (end.strftime("%Y%m%d"), f"{end.hour},{end.minute:02}")
                if end <= start:
                    return
        if end.hour > 0:
            # round down end to the nearest day midnight
            closest_day = end.replace(hour=0, minute=0)
            if closest_day >= start:
                while end > closest_day:
                    end -= one_hour
                    yield (end.strftime("%Y%m%d"), str(end.hour))
                    if end <= start:
                        return
        # round up start to the nearest end day midnight
        closest_day = start.replace(hour=0, minute=0)
        if closest_day != start:
            # only add one day if hours or minutes differ
            closest_day += one_day
        while end > closest_day:
            end -= one_day
            yield (end.strftime("%Y%m%d"), "-1")
        if end <= start:
            return
        if start.hour > 0:
            # round up start to the nearest hour
            closest_hour = start.replace(minute=0)
            if closest_hour != start:
                # only add one hour if minutes differ
                closest_hour += one_hour
            while end > closest_hour:
                end -= one_hour
                yield (end.strftime("%Y%m%d"), str(end.hour))
            if end <= start:
                return
        # finish
        while end > start:
            end -= ten_minutes
            yield (end.strftime("%Y%m%d"), f"{end.hour},{end.minute:02}")
    else:
        if start.minute > 0:
            # round up start to the nearest hour
            closest_hour = start.replace(minute=0) + one_hour
            while start < closest_hour:
                yield (start.strftime("%Y%m%d"), f"{start.hour},{start.minute:02}")
                start += ten_minutes
                if start >= end:
                    return
        if start.hour > 0:
            # round up start to the nearest day midnight
            closest_day = start.replace(hour=0, minute=0) + one_day
            if closest_day <= end:
                while start < closest_day:
                    yield (start.strftime("%Y%m%d"), str(start.hour))
                    start += one_hour
                    if start >= end:
                        return
        # round down end to the nearest end day midnight
        closest_day = end.replace(hour=0, minute=0)
        while start < closest_day:
            yield (start.strftime("%Y%m%d"), "-1")
            start += one_day
        if start >= end:
            return
        if end.hour > 0:
            # round down end to the nearest end hour
            closest_hour = end.replace(minute=0)
            while start < closest_hour:
                yield (start.strftime("%Y%m%d"), str(start.hour))
                start += one_hour
            if start >= end:
                return
        # finish
        while start < end:
            yield (start.strftime("%Y%m%d"), f"{start.hour},{start.minute:02}")
            start += ten_minutes


def get(iterable: Iterable[X], **attrs) -> Optional[X]:
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


class Lookup(Iterable[LookupType]):
    """
    A helper class utilizing an internal list and three dictionaries, allowing for easy indexing
    and lookup based on Name and ID attributes. Supports fuzzy Name searches too.

    This object resembles an immutable list, but exposes `__len__` and `__iter__` special
    methods for ease of use.
    """
    def __init__(self, iterable: Iterable[LookupType]):
        self._list_lookup: List[LookupType] = []
        self._id_lookup: Dict[int, LookupType] = {}
        self._name_lookup: Dict[str, LookupType] = {}
        self._fuzzy_lookup: Dict[str, LookupType] = {}
        for e in iterable:
            self._list_lookup.append(e)
            self._id_lookup[e.id] = e
            self._name_lookup[e.name] = e
            self._fuzzy_lookup[e.name.lower()] = e

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._list_lookup.__repr__()})"

    def __len__(self) -> int:
        """
        Returns the length of the internal list.\n
        Use ``len()`` on this object to obtain it.

        :type: int
        """
        return len(self._list_lookup)

    def __iter__(self) -> Iterator[LookupType]:
        """
        Returns an iterator over the internal list.\n
        Use ``iter()`` on this object to obtain it.

        :type: Iterator[LookupType]
        """
        return iter(self._list_lookup)

    def _lookup(self, name_or_id: Union[int, str], *, fuzzy: bool = False) -> Optional[LookupType]:
        """
        Allows you to quickly lookup an element by it's Name or ID.

        Parameters
        ----------
        name_or_id : Union[int, str]
            Name or ID of the element you want to lookup.
        fuzzy : bool
            When set to `True`, makes the Name search case insensitive.\n
            Defaults to `False`.

        Returns
        -------
        Optional[LookupType]
            The element requested.\n
            `None` is returned if the requested element couldn't be found.
        """
        if isinstance(name_or_id, int):
            return self._id_lookup.get(name_or_id)
        if fuzzy and isinstance(name_or_id, str):
            name_or_id = name_or_id.lower()
            return self._fuzzy_lookup.get(name_or_id)
        return self._name_lookup.get(name_or_id)


def chunk(list_to_chunk: List[X], chunk_length: int) -> Generator[List[X], None, None]:
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
            expanded = await element
            yield expanded
        else:
            yield element


def _int_divmod(base: Union[int, float], div: Union[int, float]) -> Tuple[int, int]:
    result = divmod(base, div)
    return (int(result[0]), int(result[1]))


class Duration:
    """
    Represents a duration. Allows for easy conversion between time units.

    This object isn't a subclass of `datetime.timedelta`, but behaves as such - it's also
    immutable, and anything you'd normally be able to do on a `datetime.timedelta` object,
    should be doable on this as well. This includes addition, substraction, multiplication,
    division (true and floor), modulo, divmod, negation and getting absolute value.
    Operations support the second argument being a normal `datetime.timedelta`,
    but the return value is always an instance of this class.
    If you prefer doing math using a normal `datetime.timedelta` object,
    you can use the `to_timedelta` method to convert it to such.
    """
    __slots__ = (
        "_delta", "_days", "_hours", "_minutes", "_seconds", "_microseconds", "_total_seconds"
    )

    def __init__(self, **kwargs):
        self._delta = timedelta(**kwargs)
        self._total_seconds = self._delta.total_seconds()
        seconds, ms_fraction = divmod(self._total_seconds, 1)
        self._microseconds = round(ms_fraction * 1e6)  # convert the fractional seconds
        minutes, seconds = _int_divmod(seconds, 60)
        self._seconds = seconds
        hours, minutes = _int_divmod(minutes, 60)
        self._minutes = minutes
        days, hours = _int_divmod(hours, 24)
        self._hours = hours
        self._days = days

    @property
    def days(self) -> int:
        """
        Returns days as an integer.

        Note: It is possible for this number to be negative, if it's been constructed from a
        negative `datetime.timedelta`.
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

    @property
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
        Converts this `Duration` object into `datetime.timedelta`.
        """
        return self._delta

    @classmethod
    def from_timedelta(cls, delta: timedelta) -> Duration:
        """
        Returns a `Duration` instance constructed from a `datetime.timedelta` object.
        """
        return cls(seconds=delta.total_seconds())

    def __repr__(self) -> str:
        args: List[Tuple[str, float]] = []
        if self._days:
            args.append(("days", self._days))
        if self._hours or self._minutes or self._seconds:
            args.append(("seconds", self._hours * 3600 + self._minutes * 60 + self._seconds))
        if self._microseconds:
            args.append(("microseconds", self._microseconds))
        return f"Duration({', '.join(f'{unit}={amount}' for unit, amount in args)})"

    def __str__(self) -> str:
        if self._days:
            s = 's' if abs(self._days) > 1 else ''
            days = f"{self._days} day{s}, "
        else:
            days = ''
        if self._hours:
            hours = f"{self._hours}:"
        else:
            hours = ''
        if self._microseconds:
            ms = f".{self._microseconds:06}"
        else:
            ms = ''
        return f"{days}{hours}{self._minutes:02}:{self._seconds:02}{ms}"

    def _get_delta(self, other: object) -> Union[timedelta, NotImplemented]:
        if isinstance(other, Duration):
            return other._delta
        elif isinstance(other, timedelta):
            return other
        return NotImplemented

    # Comparisons

    def _cmp(
        self, opr: Callable[[object, object], bool], other: object, *, base: bool = False
    ) -> bool:
        delta = self._get_delta(other)
        if delta is NotImplemented:
            if base:
                return opr is ne
            return NotImplemented
        return opr(self._delta, delta)

    __eq__ = cast(Callable[[object, object], bool], partialmethod(_cmp, eq, base=True))
    __ne__ = cast(Callable[[object, object], bool], partialmethod(_cmp, ne, base=True))
    __lt__ = partialmethod(_cmp, lt)
    __le__ = partialmethod(_cmp, le)
    __gt__ = partialmethod(_cmp, gt)
    __ge__ = partialmethod(_cmp, ge)

    # Math operations

    def __add__(self, other: Union[Duration, timedelta]) -> Duration:
        delta = self._get_delta(other)
        if delta is NotImplemented:
            return NotImplemented
        return Duration(seconds=self._total_seconds + delta.total_seconds())

    __radd__ = __add__

    def __sub__(self, other: Union[Duration, timedelta]) -> Duration:
        delta = self._get_delta(other)
        if delta is NotImplemented:
            return NotImplemented
        return Duration(seconds=self._total_seconds - delta.total_seconds())

    def __rsub__(self, other: Union[Duration, timedelta]) -> Duration:
        delta = self._get_delta(other)
        if delta is NotImplemented:
            return NotImplemented
        return Duration(seconds=delta.total_seconds() - self._total_seconds)

    def __mul__(self, other: Union[int, float]) -> Duration:
        if not isinstance(other, (int, float)):
            return NotImplemented
        return Duration(seconds=self._total_seconds * other)

    __rmul__ = __mul__

    @overload
    def __truediv__(self, other: Union[Duration, timedelta]) -> float:
        ...

    @overload
    def __truediv__(self, other: Union[int, float]) -> Duration:
        ...

    def __truediv__(self, other: Union[Duration, timedelta, int, float]):
        if isinstance(other, (int, float)):
            return Duration(seconds=self._total_seconds / other)
        delta = self._get_delta(other)
        if delta is NotImplemented:
            return NotImplemented
        return self._total_seconds / delta.total_seconds()

    def __rtruediv__(self, other: timedelta) -> float:
        if not isinstance(other, timedelta):
            return NotImplemented
        return other.total_seconds() / self._total_seconds

    @overload
    def __floordiv__(self, other: Union[Duration, timedelta]) -> int:
        ...

    @overload
    def __floordiv__(self, other: int) -> Duration:
        ...

    def __floordiv__(self, other: Union[Duration, timedelta, int]):
        if isinstance(other, int):
            return Duration(microseconds=floor(self._total_seconds * 1e6 // other))
        delta = self._get_delta(other)
        if delta is NotImplemented:
            return NotImplemented
        return int(self._total_seconds // delta.total_seconds())

    def __rfloordiv__(self, other: timedelta) -> int:
        if not isinstance(other, timedelta):
            return NotImplemented
        return int(other.total_seconds() // self._total_seconds)

    def __mod__(self, other: Union[Duration, timedelta]) -> Duration:
        delta = self._get_delta(other)
        if delta is NotImplemented:
            return NotImplemented
        return Duration(seconds=(self._total_seconds % delta.total_seconds()))

    def __rmod__(self, other: Union[Duration, timedelta]) -> Duration:
        delta = self._get_delta(other)
        if delta is NotImplemented:
            return NotImplemented
        return Duration(seconds=(delta.total_seconds() % self._total_seconds))

    def __divmod__(self, other: Union[Duration, timedelta]) -> Tuple[int, Duration]:
        delta = self._get_delta(other)
        if delta is NotImplemented:
            return NotImplemented
        q, r = divmod(self._total_seconds, delta.total_seconds())
        return (int(q), Duration(seconds=r))

    def __rdivmod__(self, other: timedelta) -> Tuple[int, Duration]:
        if not isinstance(other, timedelta):
            return NotImplemented
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


class WeakValueDefaultDict(WeakValueDictionary, Mapping[X, Y]):
    def __init__(
        self,
        default_factory: Optional[Callable[[], Any]] = None,
        mapping_or_iterable: Union[Mapping[X, Y], Iterable[Tuple[X, Y]]] = {},
    ):
        self.default_factory = default_factory
        super().__init__(mapping_or_iterable)

    def __getitem__(self, key: X) -> Y:
        try:
            return super().__getitem__(key)
        except KeyError:
            if not self.default_factory:  # pragma: no cover
                raise
            item = self.default_factory()
            self.__setitem__(key, item)
            return item
