from enum import Enum
from datetime import datetime, timedelta
from operator import attrgetter
from typing import Union, Optional, List, Iterable, Generator, AsyncGenerator

# A decorator responsible for making sure a timedelta subclass survives arthmetic operations. We have to do this since timedelta is normally immutable.
def preserve_timedelta_subclass(subclass: timedelta):
    @classmethod
    def from_timedelta(cls, delta):
        return cls(days=delta.days, seconds=delta.seconds, microseconds=delta.microseconds) #pylint: disable=no-value-for-parameter,unexpected-keyword-arg
    subclass.from_timedelta = from_timedelta

    result_list = [
        "__add__",  "__sub__",  "__mul__",  "__mod__", 
        "__radd__", "__rsub__", "__rmul__", "__rmod__",
    ]
    for method_name in result_list:
        inherited_method = getattr(super(subclass, subclass), method_name) #pylint: disable=unused-variable
        def new_method(self, other, *, inherited_method=inherited_method): #pylint: disable=function-redefined
            return self.from_timedelta(inherited_method(self, other))
        setattr(subclass, method_name, new_method)

    conditional_result_list = ["__truediv__", "__floordiv__", "__rtruediv__",]
    for method_name in conditional_result_list:
        inherited_method = getattr(super(subclass, subclass), method_name) #pylint: disable=unused-variable
        def new_method(self, other, *, inherited_method=inherited_method): #pylint: disable=function-redefined
            result = inherited_method(self, other)
            if type(result) == timedelta:
                return self.from_timedelta(result)
            return result
        setattr(subclass, method_name, new_method)
    
    divmod_list = ["__divmod__", "__rdivmod__"]
    for method_name in divmod_list:
        inherited_method = getattr(super(subclass, subclass), method_name) #pylint: disable=unused-variable
        def new_method(self, other, *, inherited_method=inherited_method): #pylint: disable=function-redefined
            q, r = inherited_method(self, other)
            if type(r) == timedelta:
                r = self.from_timedelta(r)
            return q, r
        setattr(subclass, method_name, new_method)
    
    self_list = ["__pos__", "__neg__", "__abs__"]
    for method_name in self_list:
        inherited_method = getattr(super(subclass, subclass), method_name) #pylint: disable=unused-variable
        def new_method(self, *, inherited_method=inherited_method): #pylint: disable=function-redefined
            return self.from_timedelta(inherited_method(self))
        setattr(subclass, method_name, new_method)
    
    return subclass

def convert_timestamp(timestamp: str) -> Optional[datetime]:
    """
    Converts the timestamp format returned by the API
    
    Parameters
    ----------
    timestamp : str
        The string containing the timestamp.
    
    Returns
    -------
    Optional[datetime]
        A converted datetime object.
        None is returned if an empty string was passed.
    """
    if timestamp:
        return datetime.strptime(timestamp, "%m/%d/%Y %I:%M:%S %p")

def get(iterable: Iterable, **attrs):
    """
    Returns the first object from the `iterable` which attributes match the keyword arguments passed.

    You can use `__` to search in nested attributes.
    
    Parameters
    ----------
    iterable : Iterable
        The iterable to search in.
    **attrs
        The attributes to search for.
    
    Returns
    -------
    Any
        The first object from the iterable with attributes matching the keyword arguments passed.
        None is returned if the desired object couldn't be found in the iterable.
    """
    if len(attrs) == 1: # speed up checks for only one test atribute
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
    `name` or `id` attributes. The attribute to search with is determined by the
    type of the input (int or str).
    
    Parameters
    ----------
    iterable : Iterable
        The iterable to search in.
    name_or_id : Union[str, int]
        The Name or ID of the object you're searching for.
    fuzzy : bool
        When set to True, makes the Name search case insensitive.
        Defaults to False.
    
    Returns
    -------
    Any
        The first object with matching Name or ID passed.
        None is returned if such object couldn't be found. 
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

def chunk(l: List, n: int) -> Generator[List, None, None]:
    """
    A helper generator that divides the input list into chunks of `n` length.\n
    The last chunk may be shorter than specified.
    
    Parameters
    ----------
    l : List
        The list you want to divide into chunks.
    n : int
        The length of each chunk.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]

async def expand_partial(iterable: Iterable) -> AsyncGenerator:
    """
    A helper async generator that can be used to automatically expand PartialPlayer and PartialMatch objects for you.
    Any other object found in the `iterable` is passed unchanged.

    The following classes are converted:
        PartialPlayer -> Player
        PartialMatch -> Match
    
    Parameters
    ----------
    iterable : Iterable
        The iterable containing partial objects.
    
    Returns
    -------
    AsyncGenerator
        An async generator yielding expanded versions of each partial object.
    """
    from .player import PartialPlayer # cyclic imports
    from .match import PartialMatch # cyclic imports
    for i in iterable:
        if isinstance(i, (PartialPlayer, PartialMatch)):
            p = await i.expand()
            yield p
        else:
            yield i

@preserve_timedelta_subclass
class Duration(timedelta):
    """
    Represents a duration. Allows for easy conversion between time units.
    """
    def total_days(self) -> float:
        """
        The total amount of days within the duration as a float.
        """
        return super().total_seconds() / 86400

    def total_hours(self) -> float:
        """
        The total amount of hours within the duration as a float.
        """
        return super().total_seconds() / 3600
    
    def total_minutes(self) -> float:
        """
        The total amount of minutes within the duration as a float.
        """
        return super().total_seconds() / 60
    
    def total_seconds(self) -> float:
        """
        The total amount of seconds within the duration as a float.
        """
        return super().total_seconds()
