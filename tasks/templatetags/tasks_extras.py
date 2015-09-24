__author__ = 'adrian'

from django import template
from datetime import date, timedelta

register = template.Library()


@register.filter(name='duration_str')
def duration_str(some_duration):

    days = some_duration.days
    tsecs = some_duration.total_seconds()
    hours, remainder = divmod(tsecs, 3600)
    minutes, seconds = divmod(remainder, 60)

    def fmt(n, str):
        if n > 0:
            result = "%d %s%s, " % (n, str, "" if n==1 else "s")
        else:
            result = ""
        return result

    days_str = fmt(days,"day")
    hours_str = fmt(hours,"hr")
    minutes_str = fmt(minutes,"min")
    seconds_str = fmt(seconds,"sec")

    str = days_str + hours_str + minutes_str + seconds_str
    return str[:-2] if str.endswith(', ') else str

