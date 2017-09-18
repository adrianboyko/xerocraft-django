# Standard
from datetime import date, time, timedelta, datetime
from decimal import Decimal
import calendar

# Third-Party
from nptime import nptime

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


# REVIEW: There are a few classes that have this form. Make an ABC?
def matches_weekday_of_month_pattern(pattern, d: date) -> bool:

    def nth_xday(d):
        """ Return a value which indicates that date d is the nth <x>day of the month. """
        dom_num = d.day
        ord_num = 1
        while dom_num > 7:
            dom_num -= 7
            ord_num += 1
        return ord_num

    def is_last_xday(d):
        """ Return a value which indicates whether date d is the LAST <x>day of the month. """
        month = d.month
        d += timedelta(weeks=+1)
        return d.month != month  # Don't use gt because 1 is not gt 12

    dow_num = d.weekday()  # day-of-week number
    day_matches = (dow_num == 0 and pattern.monday) \
        or (dow_num == 1 and pattern.tuesday) \
        or (dow_num == 2 and pattern.wednesday) \
        or (dow_num == 3 and pattern.thursday) \
        or (dow_num == 4 and pattern.friday) \
        or (dow_num == 5 and pattern.saturday) \
        or (dow_num == 6 and pattern.sunday)
    if not day_matches:
        return False  # Doesn't match template if day-of-week doesn't match.
    if pattern.every:
        return True  # Does match if it happens every week and the day-of-week matches.
    if is_last_xday(d) and pattern.last:
        return True  # Check for last <x>day match.

    # Otherwise, figure out the ordinal and see if we match it.
    ord_num = nth_xday(d)
    ordinal_matches = (ord_num == 1 and pattern.first) \
        or (ord_num == 2 and pattern.second) \
        or (ord_num == 3 and pattern.third) \
        or (ord_num == 4 and pattern.fourth)

    return ordinal_matches


def time_in_timespan(test_time: time, spans_start_time: time, spans_duration: timedelta) -> bool:
    test_nptime = nptime.from_time(test_time)  # type: nptime
    start_nptime = nptime.from_time(spans_start_time)  # type: nptime
    end_nptime = start_nptime + spans_duration  # type: nptime
    return start_nptime <= test_nptime < end_nptime


def currently_in_timespan(spans_start_time: time, spans_duration: timedelta) -> bool:
    test_time = datetime.now().time()  # type: time
    return time_in_timespan(test_time, spans_start_time, spans_duration)


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

