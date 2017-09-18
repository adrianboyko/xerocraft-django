# pylint: disable=E128

# Standard
from decimal import Decimal
from datetime import datetime, date, time

# Third-party
from django.db import models
from django.core.exceptions import ValidationError
from nptime import nptime

# Local
from abutils.time import (
    days_of_week_str,
    duration_single_unit_str,
    ordinals_of_month_str,
    matches_weekday_of_month_pattern,
    currently_in_timespan
)


class TimeBlockType(models.Model):

    name = models.CharField(max_length=32, null=False, blank=False,
        help_text="A short name for the time block type.")

    description = models.TextField(max_length=2048, null=False, blank=False,
        help_text="A longer description for the time block type.")

    def __str__(self):
        return self.name


class TimeBlock(models.Model):

    start_time = models.TimeField(null=True, blank=True,
        help_text="The time at which the time block begins.")

    duration = models.DurationField(null=True, blank=True,
        help_text="The duration/length of the time block (HH:MM:SS).")

    # Position in month:
    first = models.BooleanField(default=False)
    second = models.BooleanField(default=False)
    third = models.BooleanField(default=False)
    fourth = models.BooleanField(default=False)
    last = models.BooleanField(default=False)
    every = models.BooleanField(default=False)

    # Day of week:
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)

    types = models.ManyToManyField(TimeBlockType)

    @property
    def is_now(self) -> bool:
        if not matches_weekday_of_month_pattern(self, date.today()):
            return False
        return currently_in_timespan(self.start_time, self.duration)

    def clean(self):
        particular = self.first or self.second or self.third or self.fourth or self.last
        if self.every and particular:
            msg = "Doesn't make sense to combine 'Every' with some other ordinal."
            raise ValidationError(msg)

    def __str__(self):
        ords = ordinals_of_month_str(self)  # type: str
        days = days_of_week_str(self)  # type: str
        dur = duration_single_unit_str(self.duration)  # type: str
        return "{} / {} at {} for {}".format(ords, days, self.start_time, dur)