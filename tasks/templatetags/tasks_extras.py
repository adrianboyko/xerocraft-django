
# Standard
from datetime import timedelta

# Third-party
from django import template

# Local
from abutils.time import duration_single_unit_str

__author__ = 'adrian'

register = template.Library()


def pluralize(s: str, n):
    return s if n == 1 else "%ss" % s


def fmt(n, s: str):
    if n > 0:
        result = "%d %s, " % (n, pluralize(s, n))
    else:
        result = ""
    return result


@register.filter(name='duration_str')
def duration_str(d: timedelta) -> str:

    days = d.days
    tsecs = d.total_seconds()
    hours, remainder = divmod(tsecs, 3600)
    minutes, seconds = divmod(remainder, 60)

    days_str = fmt(days, "day")
    hours_str = fmt(hours, "hr")
    minutes_str = fmt(minutes, "min")
    seconds_str = fmt(seconds, "sec")

    s = days_str + hours_str + minutes_str + seconds_str
    return s[:-2] if s.endswith(', ') else s


@register.filter(name='duration_str2')
def duration_str2(d: timedelta):
    duration_single_unit_str(d)