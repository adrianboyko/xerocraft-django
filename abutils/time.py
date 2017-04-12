# Standard
from datetime import date, timedelta
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
