from __future__ import annotations

import pytest
from arez.mixins import CacheObject
from arez.utils import Lookup, LookupGroup


class Element(CacheObject):
    def __init__(self, id: int, name: str, element: Element):
        super().__init__(id=id, name=name)
        self.element: Element = element

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"

    def __eq__(self, other: object):
        if isinstance(other, int):
            return self.id == other  # compare with integers
        return NotImplemented

    __hash__ = CacheObject.__hash__


zero = Element(0, "Zero", None)  # type: ignore
zero.element = zero
one = Element(1, "One", zero)
original = [
    one,
    Element(3, "Three", zero),
    Element(2, "Two", zero),
    Element(4, "Four", one),
    Element(5, "Five", one),
]
lcp1 = Lookup(original)


def test_lookup():
    assert str(lcp1) == ("Lookup([Element(1), Element(3), Element(2), Element(4), Element(5)])")
    # test ID get
    assert lcp1.get(4) == 4
    # test name get
    assert lcp1.get("tow") is None
    assert lcp1.get("Two") == 2
    # test fuzzy name get
    assert lcp1.get_fuzzy("two") == 2
    assert lcp1.get_fuzzy("six") is None
    # test fuzzy with scores - first from the list, first from the 2-item tuple
    cutoff = 0.6
    matches = lcp1.get_fuzzy_matches("tow", cutoff=cutoff, with_scores=True)
    first = matches[0]
    assert first[0] == 2
    assert first[1] >= cutoff
    # test len
    assert len(lcp1) == len(original)
    # test contains
    assert original[0] in lcp1
    # test count
    assert lcp1.count(original[0]) == 1
    # test internal list order, reversed and indexing
    lcp_len = len(lcp1) // 2 + 1
    for i, ri, it, rit, org, rorg in zip(
        range(lcp_len),  # enumerate
        range(len(lcp1)-1, -1, -1),  # noqa, reverse enumerate
        lcp1,  # lookup
        reversed(lcp1),  # reverse lookup
        original,
        reversed(original),
    ):
        assert it == org  # lookup vs original
        assert lcp1[i] == original[i]  # order lookup vs original
        assert lcp1.index(it) == i  # index
        assert rit == rorg  # reversed lookup vs reversed original
        assert lcp1[ri] == original[ri]  # order reversed lookup vs reversed original

    # test out-of-bounds index error
    with pytest.raises(IndexError):
        lcp1[len(original)]
    # test fuzzy type errors
    with pytest.raises(TypeError):  # name
        lcp1.get_fuzzy_matches(123)  # type: ignore
    with pytest.raises(TypeError):  # limit
        lcp1.get_fuzzy_matches("test", limit="yes")  # type: ignore
    with pytest.raises(TypeError):  # cutoff
        lcp1.get_fuzzy_matches("test", cutoff="yes")  # type: ignore
    # test fuzzy value errors
    with pytest.raises(ValueError):  # limit
        lcp1.get_fuzzy_matches("test", limit=-1)
    with pytest.raises(ValueError):  # limit
        lcp1.get_fuzzy_matches("test", cutoff=3.5)
    # test creation with non-CacheObject
    with pytest.raises(ValueError):
        Lookup([1, 2, 3])

    # test LookupGroup
    lcp2 = LookupGroup(original, key=lambda item: item.element)
    zero_group = lcp2.get(0)
    one_group = lcp2.get(1)
    assert zero_group is not None and len(zero_group) == 3
    assert one_group is not None and len(one_group) == 2
    with pytest.raises(ValueError):
        LookupGroup([1, 2, 3])
