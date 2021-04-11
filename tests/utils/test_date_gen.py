from datetime import timedelta

import pytest
from arez.utils import _date_gen

from ..conftest import BASE_DATETIME


@pytest.mark.api()
@pytest.mark.base()
@pytest.mark.slow()
def test_date_gen():
    # helpful time intervals
    one_day = timedelta(days=1)
    one_hour = timedelta(hours=1)

    # 0 width time slice
    start = BASE_DATETIME
    end = BASE_DATETIME
    for date, hour in _date_gen(start=start, end=end):
        assert False, "0 width time slice wasn't supposed to run"

    # main test, 10m, 1h, 1d, 1h, 10m
    start = BASE_DATETIME + timedelta(hours=22, minutes=50)
    end = BASE_DATETIME + timedelta(days=2, hours=1, minutes=10)
    for n, (date, hour) in enumerate(_date_gen(start=start, end=end)):
        if n <= 1:
            assert date == start.strftime("%Y%m%d")
        elif n == 2:
            assert date == (BASE_DATETIME + one_day).strftime("%Y%m%d")
        else:
            assert date == end.strftime("%Y%m%d")
        if n == 0:
            assert hour == "22,50"
        elif n == 1:
            assert hour == "23"
        elif n == 2:
            assert hour == "-1"
        elif n == 3:
            assert hour == "0"
        elif n == 4:
            assert hour == "1,00"
        else:
            assert False, "date_gen tried to end later than expected"
    assert n == 4, "date_gen ended earlier than expected"
    # 10m initial interval exit
    ran = False
    start = BASE_DATETIME + timedelta(minutes=50)
    end = BASE_DATETIME + one_hour
    for date, hour in _date_gen(start=start, end=end):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "0,50"
        ran = True
    assert ran, "date_gen ended earlier than expected"
    # 1h initial interval exit
    ran = False
    start = BASE_DATETIME + timedelta(hours=23)
    end = BASE_DATETIME + one_day
    for date, hour in _date_gen(start=start, end=end):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "23"
        ran = True
    assert ran, "date_gen ended earlier than expected"
    # 1d interval exit
    ran = False
    start = BASE_DATETIME
    end = BASE_DATETIME + one_day
    for date, hour in _date_gen(start=start, end=end):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "-1"
        ran = True
    assert ran, "date_gen ended earlier than expected"
    # 1h finishing interval exit
    ran = False
    start = BASE_DATETIME
    end = BASE_DATETIME + one_hour
    for date, hour in _date_gen(start=start, end=end):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "0"
        ran = True
    assert ran, "date_gen ended earlier than expected"
    # 1h->10m corner case
    ran = False
    start = BASE_DATETIME + one_hour
    end = BASE_DATETIME + timedelta(hours=1, minutes=10)
    for date, hour in _date_gen(start=start, end=end):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "1,00"
        ran = True
    assert ran, "date_gen ended earlier than expected"

    # main test, 10m, 1h, 1d, 1h, 10m, reverse
    start = BASE_DATETIME + timedelta(hours=22, minutes=50)
    end = BASE_DATETIME + timedelta(days=2, hours=1, minutes=10)
    for n, (date, hour) in enumerate(_date_gen(start=start, end=end, reverse=True)):
        if n <= 1:
            assert date == end.strftime("%Y%m%d")
        elif n == 2:
            assert date == (BASE_DATETIME + one_day).strftime("%Y%m%d")
        else:
            assert date == start.strftime("%Y%m%d")
        if n == 0:
            assert hour == "1,00"
        elif n == 1:
            assert hour == "0"
        elif n == 2:
            assert hour == "-1"
        elif n == 3:
            assert hour == "23"
        elif n == 4:
            assert hour == "22,50"
        else:
            assert False, "date_gen tried to end later than expected"
    assert n == 4, "date_gen ended earlier than expected"
    # 10m initial interval exit, reverse
    ran = False
    start = BASE_DATETIME + one_hour
    end = BASE_DATETIME + timedelta(hours=1, minutes=10)
    for date, hour in _date_gen(start=start, end=end, reverse=True):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "1,00"
        ran = True
    assert ran, "date_gen ended earlier than expected"
    # 1h initial interval exit, reverse
    ran = False
    start = BASE_DATETIME
    end = BASE_DATETIME + timedelta(hours=1)
    for date, hour in _date_gen(start=start, end=end, reverse=True):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "0"
        ran = True
    assert ran, "date_gen ended earlier than expected"
    # 1d interval exit, reverse
    ran = False
    start = BASE_DATETIME
    end = BASE_DATETIME + one_day
    for date, hour in _date_gen(start=start, end=end, reverse=True):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "-1"
        ran = True
    assert ran, "date_gen ended earlier than expected"
    # 1h finishing interval exit, reverse
    ran = False
    start = BASE_DATETIME + timedelta(hours=23)
    end = BASE_DATETIME + one_day
    for date, hour in _date_gen(start=start, end=end, reverse=True):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "23"
        ran = True
    assert ran, "date_gen ended earlier than expected"
    # 1h->10m corner case
    ran = False
    start = BASE_DATETIME + timedelta(minutes=50)
    end = BASE_DATETIME + one_hour
    for date, hour in _date_gen(start=start, end=end, reverse=True):
        assert not ran, "date_gen tried to end later than expected"
        assert date == start.strftime("%Y%m%d")
        assert hour == "0,50"
        ran = True
    assert ran, "date_gen ended earlier than expected"
