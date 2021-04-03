from collections import namedtuple

import arez
import pytest


_TestItem = namedtuple("_TestItem", ["id", "name", "item"])

zero = _TestItem(0, "zero", None)

_test_list = [
    _TestItem(1, "one", zero),
    _TestItem(2, "two", zero),
    _TestItem(3, "three", zero),
    _TestItem(4, "four", _TestItem(5, "five", None)),
]


def test_get():
    get = arez.utils.get
    # test id
    item = get(_test_list, id=1)
    assert item is _test_list[0]
    # test none
    item = get(_test_list, name="test")
    assert item is None
    # test double: id and name
    item = get(_test_list, id=3, name="three")
    assert item is _test_list[2]
    # test double: none
    item = get(_test_list, id=3, name="six")
    assert item is None
    # test nested item
    item = get(_test_list, item__id=5)
    assert item is _test_list[3]


@pytest.mark.vcr()
@pytest.mark.asyncio()
@pytest.mark.dependency(depends=["tests/test_player.py::test_player_history"], scope="session")
async def test_expand_partial(player: arez.PartialPlayer):
    expand_partial = arez.utils.expand_partial
    history = await player.get_match_history()

    mixed_list = [history[0], 123]

    async for match in expand_partial(mixed_list):
        assert not isinstance(match, arez.PartialMatch)
