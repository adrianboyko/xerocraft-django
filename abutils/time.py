# Standard
from datetime import date, timedelta
import calendar

# Third-Party

# Local


def is_last_day_of_month(curr_date: date):
    next_day = curr_date + timedelta(days=1)  # type: date
    return next_day.month != curr_date.month


# E.g. is_nth_day(date.today(), 3, 3) returns true if today is the 3rd Thursday of the month.
# Note that Monday is 0, Tuesday is 1, etc...
def is_nth_day(date_in_question: date, nth: int, daynum: int) -> bool:
    return date_in_question == calendar.Calendar(nth).monthdatescalendar(
        date_in_question.year,
        date_in_question.month
    )[daynum][0]
