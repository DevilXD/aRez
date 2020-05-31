import pytest
from arez.utils import Lookup


class Element:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id}, {self.name})"

    def __eq__(self, other):
        return self.id == other  # compare with integers


lcp = Lookup([
    Element(1, "One"),
    Element(3, "Three"),
    Element(2, "Two"),
    Element(4, "Four"),
    Element(5, "Five"),
])


@pytest.mark.dependency(scope="session")
def test_lookup():
    assert str(lcp) == (
        "Lookup([Element(1, One), Element(3, Three), Element(2, Two), "
        "Element(4, Four), Element(5, Five)])"
    )
    assert lcp._lookup(4) == 4
    assert lcp._lookup("two") is None
    assert lcp._lookup("Two") == 2
    assert lcp._lookup("two", fuzzy=True) == 2
    assert lcp._lookup("six", fuzzy=True) is None
