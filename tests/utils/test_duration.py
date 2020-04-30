# mypy: allow-redefinition

from math import floor
from datetime import timedelta

from arez.utils import Duration


d0 = Duration(hours=1)
d1 = Duration(minutes=20)
d2 = timedelta(seconds=4)


def test_addition():
    d3 = d0 + d1
    d4 = d1 + d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 80 * 60
    assert isinstance(d4, Duration) and d4.total_seconds() == 80 * 60

    d3 = d0 + d2
    d4 = d2 + d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 60 * 60 + 4
    assert isinstance(d4, Duration) and d4.total_seconds() == 60 * 60 + 4

    d3 = d1 + d2
    d4 = d2 + d1
    assert isinstance(d3, Duration) and d3.total_seconds() == 20 * 60 + 4
    assert isinstance(d4, Duration) and d4.total_seconds() == 20 * 60 + 4


def test_substraction():
    d3 = d0 - d1
    d4 = d1 - d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 40 * 60
    assert isinstance(d4, Duration) and d4.total_seconds() == -40 * 60

    d3 = d0 - d2
    d4 = d2 - d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 60 * 60 - 4
    assert isinstance(d4, Duration) and d4.total_seconds() == 4 - 60 * 60

    d3 = d1 - d2
    d4 = d2 - d1
    assert isinstance(d3, Duration) and d3.total_seconds() == 20 * 60 - 4
    assert isinstance(d4, Duration) and d4.total_seconds() == 4 - 20 * 60


def test_multiplication():
    d3 = d0 * 3
    d4 = 3 * d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 60 * 60 * 3
    assert isinstance(d4, Duration) and d4.total_seconds() == 60 * 60 * 3

    d3 = d0 * 2.34
    d4 = 2.34 * d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 60 * 60 * 2.34
    assert isinstance(d4, Duration) and d4.total_seconds() == 60 * 60 * 2.34


def test_division():
    d3 = d0 / 3
    d4 = d0 / 2.34
    assert isinstance(d3, Duration) and d3.total_seconds() == 20 * 60
    assert isinstance(d4, Duration) and d4.total_seconds() == round((60 * 60) / 2.34, 6)

    d3 = d0 / d1
    d4 = d1 / d0
    assert isinstance(d3, float) and d3 == 3
    assert isinstance(d4, float) and d4 == 1 / 3

    d3 = d0 / d2
    d4 = d2 / d0
    assert isinstance(d3, float) and d3 == 900
    assert isinstance(d4, float) and d4 == 1 / 900


def test_modulo():
    d3 = d0 % d1
    d4 = d1 % d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 0
    assert isinstance(d4, Duration) and d4.total_seconds() == 20 * 60

    d3 = d0 % d2
    d4 = d2 % d0
    assert isinstance(d3, Duration) and d3.total_seconds() == 0
    assert isinstance(d4, Duration) and d4.total_seconds() == 4

    d3 = d1 % d2
    d4 = d2 % d1
    assert isinstance(d3, Duration) and d3.total_seconds() == 0
    assert isinstance(d4, Duration) and d4.total_seconds() == 4


def test_intdiv():
    d3 = d0 // 3599
    d4 = d0 / 3599
    assert isinstance(d3, Duration) and d3.total_seconds() == floor(3600 * 1e6 // 3599) / 1e6
    assert isinstance(d4, Duration) and d4.total_seconds() == round(3600 * 1e6 / 3599) / 1e6

    d3 = d0 // d1
    d4 = d1 // d0
    assert isinstance(d3, int) and d3 == 3
    assert isinstance(d4, int) and d4 == 0

    d3 = d0 // d2
    d4 = d2 // d0
    assert isinstance(d3, int) and d3 == 900
    assert isinstance(d4, int) and d4 == 0


def test_divmod():
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


def test_signs():
    d3 = +d0
    d4 = -d0
    d5 = abs(d4)
    assert isinstance(d3, Duration) and d3 is not d0 and d3.total_seconds() == 60 * 60
    assert isinstance(d4, Duration) and d4 is not d0 and d4.total_seconds() == -60 * 60
    assert isinstance(d5, Duration) and d5 is not d0 and d5.total_seconds() == 60 * 60


def test_text():
    assert repr(d0) == "Duration(seconds=3600)"
    assert str(d0) == "1:00:00"
    assert repr(d1) == "Duration(seconds=1200)"
    assert str(d1) == "20:00"
    d3 = Duration.from_timedelta(d2)
    assert repr(d3) == "Duration(seconds=4)"
    assert str(d3) == "00:04"
