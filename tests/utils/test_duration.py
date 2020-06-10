# mypy: allow-redefinition

from math import floor
from datetime import timedelta

import pytest
from arez.utils import Duration


d0 = Duration(hours=1)
d1 = Duration(minutes=20)
d2 = timedelta(seconds=4)


def test_comparisons():
    # eq
    assert d0 == Duration(hours=1)
    assert d0 == timedelta(hours=1)
    # ne
    assert d0 != d1
    assert d0 != d2
    # lt
    assert d1 < d0
    assert d1 < timedelta(hours=1)
    # le
    assert d1 <= d0
    assert d1 <= d1
    assert d1 <= timedelta(hours=1)
    assert d1 <= timedelta(minutes=20)
    # gt
    assert d0 > d1
    assert d0 > timedelta(minutes=20)
    # ge
    assert d0 >= d1
    assert d0 >= d0
    assert d0 >= timedelta(minutes=20)
    assert d0 >= timedelta(hours=1)
    # NotImplemented
    assert (d0 == None) is False  # noqa
    assert (d0 != None) is True  # noqa
    # other comparisons raise TypeError
    with pytest.raises(TypeError):
        d0 < None
    with pytest.raises(TypeError):
        d0 <= None
    with pytest.raises(TypeError):
        d0 > None
    with pytest.raises(TypeError):
        d0 >= None


def test_addition():
    # Duration + Duration
    d3 = d0 + d1
    d4 = d1 + d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 80 * 60
    assert isinstance(d4, Duration) and d4.total_seconds() == 80 * 60

    # Duration + timedelta
    d3 = d1 + d2
    d4 = d2 + d1
    assert isinstance(d3, Duration) and d3.total_seconds() == 20 * 60 + 4
    assert isinstance(d4, Duration) and d4.total_seconds() == 20 * 60 + 4

    # Duration + NotImplemented, NotImplemented + Duration
    with pytest.raises(TypeError):
        d3 = d0 + None  # type: ignore
    with pytest.raises(TypeError):
        d4 = None + d0  # type: ignore


def test_substraction():
    # Duration - Duration
    d3 = d0 - d1
    d4 = d1 - d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 40 * 60
    assert isinstance(d4, Duration) and d4.total_seconds() == -40 * 60

    # Duration - timedelta, timedelta - Duration
    d3 = d0 - d2
    d4 = d2 - d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 60 * 60 - 4
    assert isinstance(d4, Duration) and d4.total_seconds() == 4 - 60 * 60

    # Duration - NotImplemented, NotImplemented - Duration
    with pytest.raises(TypeError):
        d3 = d0 - None  # type: ignore
    with pytest.raises(TypeError):
        d4 = None - d0  # type: ignore


def test_multiplication():
    # Duration * int, int * Duration
    d3 = d0 * 3
    d4 = 3 * d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 60 * 60 * 3
    assert isinstance(d4, Duration) and d4.total_seconds() == 60 * 60 * 3

    # Duration * float, float * Duration
    d3 = d0 * 2.34
    d4 = 2.34 * d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 60 * 60 * 2.34
    assert isinstance(d4, Duration) and d4.total_seconds() == 60 * 60 * 2.34

    # Duration * NotImplemented, NotImplemented * Duration
    with pytest.raises(TypeError):
        d3 = d0 * None  # type: ignore
    with pytest.raises(TypeError):
        d4 = None * d0  # type: ignore


def test_division():
    # Duration / int, Duration / float
    d3 = d0 / 3
    d4 = d0 / 2.34
    assert isinstance(d3, Duration) and d3.total_seconds() == 20 * 60
    assert isinstance(d4, Duration) and d4.total_seconds() == round((60 * 60) / 2.34, 6)

    # Duration / Duration
    d3 = d0 / d1
    d4 = d1 / d0
    assert isinstance(d3, float) and d3 == 3
    assert isinstance(d4, float) and d4 == 1 / 3

    # Duration / timedelta, timedelta / Duration
    d3 = d0 / d2
    d4 = d2 / d0
    assert isinstance(d3, float) and d3 == 900
    assert isinstance(d4, float) and d4 == 1 / 900

    # Duration / NotImplemented, NotImplemented / Duration
    with pytest.raises(TypeError):
        d3 = d0 / None  # type: ignore
    with pytest.raises(TypeError):
        d4 = None / d0  # type: ignore


def test_modulo():
    # Duration % Duration
    d3 = d0 % d1
    d4 = d1 % d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 0
    assert isinstance(d4, Duration) and d4.total_seconds() == 20 * 60

    # Duration % timedelta, timedelta % Duration
    d3 = d0 % d2
    d4 = d2 % d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 0
    assert isinstance(d4, Duration) and d4.total_seconds() == 4

    # Duration % NotImplemented, NotImplemented % Duration
    with pytest.raises(TypeError):
        d3 = d0 % None  # type: ignore
    with pytest.raises(TypeError):
        d4 = None % d0  # type: ignore


def test_intdiv():
    # Duration // int, compare to normal division
    d3 = d0 // 3599
    d4 = d0 / 3599
    assert isinstance(d3, Duration) and d3.total_seconds() == floor(3600 * 1e6 // 3599) / 1e6
    assert isinstance(d4, Duration) and d4.total_seconds() == round(3600 * 1e6 / 3599) / 1e6

    # Duration // Duration
    d3 = d0 // d1
    d4 = d1 // d0
    assert isinstance(d3, int) and d3 == 3
    assert isinstance(d4, int) and d4 == 0

    # Duration // timedelta, timedelta // Duration
    d3 = d0 // d2
    d4 = d2 // d0
    assert isinstance(d3, int) and d3 == 900
    assert isinstance(d4, int) and d4 == 0

    # Duration // NotImplemented, NotImplemented // Duration
    with pytest.raises(TypeError):
        d3 = d0 // None  # type: ignore
    with pytest.raises(TypeError):
        d4 = None // d0  # type: ignore


def test_divmod():
    # divmod(Duration, Duration)
    n1, r1 = divmod(d0, d1)
    n2, r2 = divmod(d1, d0)
    assert (
        isinstance(n1, int)
        and isinstance(r1, Duration)
        and n1 == 3
        and r1.total_seconds() == 0
    )
    assert (
        isinstance(n2, int)
        and isinstance(r2, Duration)
        and n2 == 0
        and r2.total_seconds() == 20 * 60
    )

    # divmod(Duration, timedelta), divmod(timedelta, Duration)
    n1, r1 = divmod(d0, d2)
    n2, r2 = divmod(d2, d0)
    assert (
        isinstance(n1, int)
        and isinstance(r1, Duration)
        and n1 == 900
        and r1.total_seconds() == 0
    )
    assert (
        isinstance(n2, int)
        and isinstance(r2, Duration)
        and n2 == 0
        and r2.total_seconds() == 4
    )

    # divmod(Duration, NotImplemented), divmod(NotImplemented, Duration)
    with pytest.raises(TypeError):
        n1, r1 = divmod(d0, None)  # type: ignore
    with pytest.raises(TypeError):
        n2, r2 = divmod(None, d0)  # type: ignore


def test_signs():
    d3 = +d0
    d4 = -d0
    d5 = abs(d4)
    d6 = abs(d0)
    assert isinstance(d3, Duration) and d3 is not d0 and d3.total_seconds() == 60 * 60
    assert isinstance(d4, Duration) and d4 is not d0 and d4.total_seconds() == -60 * 60
    assert isinstance(d5, Duration) and d5 is not d0 and d5.total_seconds() == 60 * 60
    assert isinstance(d6, Duration) and d6 is not d0 and d6.total_seconds() == 60 * 60


def test_attributes_methods():
    assert d0.microseconds == 0
    assert d0.seconds == 0
    assert d0.minutes == 0
    assert d0.hours == 1
    assert d0.days == 0
    assert d0.total_days() == 1 / 24
    assert d0.total_hours() == 1.0
    assert d0.total_minutes() == 60.0
    assert d0.total_seconds() == 60 * 60.0
    assert d0.to_timedelta() == timedelta(hours=1)


def test_text():
    assert repr(d0) == "Duration(seconds=3600)"
    assert str(d0) == "1:00:00"
    assert repr(d1) == "Duration(seconds=1200)"
    assert str(d1) == "20:00"
    d3 = Duration.from_timedelta(d2)
    assert repr(d3) == "Duration(seconds=4)"
    assert str(d3) == "00:04"
    d4 = Duration(days=1, microseconds=1)
    assert repr(d4) == "Duration(days=1, microseconds=1)"
    assert str(d4) == "1 day, 00:00.000001"
