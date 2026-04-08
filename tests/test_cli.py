from datetime import datetime
import pytest

from first_filings.cli import get_date_range


def test_get_date_range_day():
    date_obj = datetime(2023, 10, 25)
    from_date, to_date = get_date_range(date_obj, "day")
    assert from_date == date_obj
    assert to_date == date_obj


def test_get_date_range_wtd():
    # Wednesday
    date_obj = datetime(2023, 10, 25)
    from_date, to_date = get_date_range(date_obj, "wtd")
    # Monday of that week
    assert from_date == datetime(2023, 10, 23)
    assert to_date == date_obj

    # Monday
    date_obj_mon = datetime(2023, 10, 23)
    from_date_mon, to_date_mon = get_date_range(date_obj_mon, "wtd")
    assert from_date_mon == datetime(2023, 10, 23)
    assert to_date_mon == date_obj_mon

    # Sunday
    date_obj_sun = datetime(2023, 10, 29)
    from_date_sun, to_date_sun = get_date_range(date_obj_sun, "wtd")
    assert from_date_sun == datetime(2023, 10, 23)
    assert to_date_sun == date_obj_sun


def test_get_date_range_mtd():
    date_obj = datetime(2023, 10, 25)
    from_date, to_date = get_date_range(date_obj, "mtd")
    assert from_date == datetime(2023, 10, 1)
    assert to_date == date_obj

    # 1st of the month
    date_obj_1st = datetime(2023, 10, 1)
    from_date_1st, to_date_1st = get_date_range(date_obj_1st, "mtd")
    assert from_date_1st == datetime(2023, 10, 1)
    assert to_date_1st == date_obj_1st


def test_get_date_range_qtd():
    # Q1: January - March
    date_obj_q1 = datetime(2023, 2, 15)
    from_date, to_date = get_date_range(date_obj_q1, "qtd")
    assert from_date == datetime(2023, 1, 1)
    assert to_date == date_obj_q1

    # Q2: April - June
    date_obj_q2 = datetime(2023, 5, 10)
    from_date, to_date = get_date_range(date_obj_q2, "qtd")
    assert from_date == datetime(2023, 4, 1)
    assert to_date == date_obj_q2

    # Q3: July - September
    date_obj_q3 = datetime(2023, 9, 30)
    from_date, to_date = get_date_range(date_obj_q3, "qtd")
    assert from_date == datetime(2023, 7, 1)
    assert to_date == date_obj_q3

    # Q4: October - December
    date_obj_q4 = datetime(2023, 12, 31)
    from_date, to_date = get_date_range(date_obj_q4, "qtd")
    assert from_date == datetime(2023, 10, 1)
    assert to_date == date_obj_q4


def test_get_date_range_invalid_period():
    date_obj = datetime(2023, 10, 25)
    with pytest.raises(ValueError, match="Invalid period: ytd"):
        get_date_range(date_obj, "ytd")
