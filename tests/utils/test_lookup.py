import pytest
from arez.utils import Lookup
from arez.mixins import CacheObject


class Element(CacheObject):
    def __init__(self, id, name):
        super().__init__(id=id, name=name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id}, {self.name})"

    def __eq__(self, other):
        return self.id == other  # compare with integers

    __hash__ = CacheObject.__hash__


original = [
    Element(1, "One"),
    Element(3, "Three"),
    Element(2, "Two"),
    Element(4, "Four"),
    Element(5, "Five"),
]

lcp = Lookup(original)


@pytest.mark.dependency(scope="session")
def test_lookup():
    assert str(lcp) == (
        "Lookup([Element(1, One), Element(3, Three), Element(2, Two), "
        "Element(4, Four), Element(5, Five)])"
    )
    assert lcp.get(4) == 4
    assert lcp.get("two") is None
    assert lcp.get("Two") == 2
    assert lcp.get("two", fuzzy=True) == 2
    assert lcp.get("six", fuzzy=True) is None
    assert len(lcp) == len(original)
    for i, it1, it2 in zip(range(len(lcp)), lcp, original):
        assert it1 == it2
        assert lcp[i] == original[i]
    with pytest.raises(IndexError):
        lcp[len(original)]
