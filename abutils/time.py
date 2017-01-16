# Standard
from datetime import date, timedelta

# Third-Party

# Local


def is_last_day_of_month(curr_date: date):
    next_day = curr_date + timedelta(days=1)  # type: date
    return next_day.month != curr_date.month
