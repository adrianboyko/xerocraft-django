# Standard
from datetime import date, timedelta
from decimal import Decimal
import calendar

# Third-Party

# Local


def is_very_last_day_of_month(some_date: date) -> bool:
    future_day = some_date + timedelta(days=1)  # type: date
    return future_day.month != some_date.month


def is_last_xxxday_of_month(some_date: date) -> bool:
    """True if the given date is the last {mon|tues|...|sun}day of the month"""
    future_xxxday = some_date + timedelta(days=7)  # type: date
    return future_xxxday.month != some_date.month


def is_nth_xxxday_of_month(some_date: date, nth: int) -> bool:
    """True if the given date is the nth {mon|tues|...|sun}day of the month"""
    past_xxxday = some_date - nth * timedelta(days=7)  # type: date
    result = is_last_xxxday_of_month(past_xxxday)
    return result


# REVIEW: There are a few classes that have this form. Make an ABC?
def days_of_week_str(obj) -> str:
    blank = '\u25CC'
    return "%s%s%s%s%s%s%s" % (
        "S" if obj.sunday else blank,
        "M" if obj.monday else blank,
        "T" if obj.tuesday else blank,
        "W" if obj.wednesday else blank,
        "T" if obj.thursday else blank,
        "F" if obj.friday else blank,
        "S" if obj.saturday else blank,
    )


# REVIEW: There are a few classes that have this form. Make an ABC?
def ordinals_of_month_str(obj) -> str:
    blank = '\u25CC'
    if obj.every:
        return "Every"
    else:
        return "%s%s%s%s%s" % (
            "1" if obj.first else blank,
            "2" if obj.second else blank,
            "3" if obj.third else blank,
            "4" if obj.fourth else blank,
            "L" if obj.last else blank,
        )


def duration_single_unit_str(d: timedelta) -> str:

    def pluralize(s: str, n):
        return s if n == 1 else "%ss" % s

    """Generates strings like '3.5 hours', '2 minutes', '22.5 seconds'"""
    tsecs = Decimal(d.total_seconds())
    tmins = tsecs / Decimal("60")
    thours = tsecs / Decimal("3600")
    if thours >= 1:
        val, unit = thours, pluralize("hr", thours)
    elif tmins >= 1:
        val, unit = tmins, pluralize("min", tmins)
    else:
        val, unit = tsecs, pluralize("sec", tsecs)
    valstr = '%g' % val  # Format with no trailing zeros
    return "%s %s" % (valstr, unit)

