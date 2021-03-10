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
    # test ID get
    assert lcp.get(4) == 4
    # test name get
    assert lcp.get("two") is None
    assert lcp.get("Two") == 2
    # test fuzzy name get
    assert lcp.get_fuzzy_one("two") == 2
    assert lcp.get_fuzzy_one("six") is None
    # test fuzzy with scores - first from the list, first from the 2-item tuple
    assert lcp.get_fuzzy("tow", with_scores=True)[0][0] == 2
    # test len
    assert len(lcp) == len(original)
    # test internal list order and indexing
    for i, it1, it2 in zip(range(len(lcp)), lcp, original):
        assert it1 == it2
        assert lcp[i] == original[i]

    # test out-of-bounds index error
    with pytest.raises(IndexError):
        lcp[len(original)]
    # test fuzzy type errors
    with pytest.raises(TypeError):  # name
        lcp.get_fuzzy(123)  # type: ignore
    with pytest.raises(TypeError):  # limit
        lcp.get_fuzzy("test", limit="yes")  # type: ignore
    with pytest.raises(TypeError):  # cutoff
        lcp.get_fuzzy("test", cutoff="yes")  # type: ignore
    # test fuzzy value errors
    with pytest.raises(ValueError):  # limit
        lcp.get_fuzzy("test", limit=-1)
    with pytest.raises(ValueError):  # limit
        lcp.get_fuzzy("test", cutoff=3.5)
