__author__ = 'adrian'

from django import template
import numbers
from decimal import *


register = template.Library()


def pluralize(str, n):
    return str if n==1 else "%ss"%str


def fmt(n, str):
    if n > 0:
        result = "%d %s, " % (n, pluralize(str,n))
    else:
        result = ""
    return result


@register.filter(name='duration_str')
def duration_str(some_duration):

    days = some_duration.days
    tsecs = some_duration.total_seconds()
    hours, remainder = divmod(tsecs, 3600)
    minutes, seconds = divmod(remainder, 60)

    days_str = fmt(days,"day")
    hours_str = fmt(hours,"hr")
    minutes_str = fmt(minutes,"min")
    seconds_str = fmt(seconds,"sec")

    str = days_str + hours_str + minutes_str + seconds_str
    return str[:-2] if str.endswith(', ') else str


@register.filter(name='duration_str2')
def duration_str2(some_duration):
    tsecs = Decimal(some_duration.total_seconds())
    tmins = tsecs / Decimal(60)
    thours = tsecs / Decimal(3600)
    if thours >= 1: val, unit = thours, pluralize("hr", thours)
    elif tmins >= 1: val, unit = tmins, pluralize("min", tmins)
    else: val, unit = tsecs, pluralize("sec", tsecs)
    valstr = '%g'%val  # Format with no trailing zeros
    return "%s %s" % (valstr, unit)
