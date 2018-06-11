
# Standard
from datetime import datetime, date

# Third-party
from django.db import models

# Local
from books.models import SaleLineItem
from members.models import Member


class OnAirPersonality (models.Model):

    member = models.ForeignKey(Member, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The member who is authorized to be on air.")

    moniker = models.CharField(max_length=40,
        help_text="Moniker/nickname such as 'The Vinyl Wizard'.")

    bio = models.TextField(max_length=2048,
        help_text="Biographical info for public consumption.")

    active = models.BooleanField(default=True,
        help_text="Checked if this person is still active.")


class Show (models.Model):

    title = models.CharField(max_length=80,
        help_text="A short description/name for the task.")

    start_time = models.TimeField(null=False, blank=False,
        help_text="The time at which the show begins.")

    minute_duration = models.IntegerField(null=False, blank=False,
        help_text="The duration of the show in MINUTES.")

    mondays = models.BooleanField(default=False)
    tuesdays = models.BooleanField(default=False)
    wednesdays = models.BooleanField(default=False)
    thursdays = models.BooleanField(default=False)
    fridays = models.BooleanField(default=False)
    saturdays = models.BooleanField(default=False)
    sundays = models.BooleanField(default=False)

    hosts = models.ManyToManyField(OnAirPersonality,
        help_text="Host of the show.")

    active = models.BooleanField(default=True,
        help_text="Checked if this show is still active.")


class UnderwritingAgreement (SaleLineItem):

    start_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="The first day on which a spot can run.")

    end_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="The last day on which a spot can run.")

    spot_seconds = models.IntegerField(null=False, blank=False,
        help_text="The length of each spot in seconds.")

    DAYTIME    = "DAY"
    DRIVETIME  = "DRV"
    SHOWTIME   = "SHW"
    CUSTOMTIME = "CST"
    TIME_CHOICES = [
        (DAYTIME,    "Daytime"),
        (DRIVETIME,  "Drivetime"),
        (DRIVETIME,  "Specific Show"),
        (CUSTOMTIME, "Custom Time")
    ]
    time = models.CharField(max_length=3, choices=TIME_CHOICES, null=False, blank=False,
        help_text="The time during which the spot can air.")

    specific_show = models.ForeignKey(Show, null=True, blank=True,
        on_delete=models.PROTECT,  # Don't allow show to be deleted if it's referenced.
        help_text="If spots MUST run during some specific show, select one.")


class UnderwritingLog (models.Model):

    agreement = models.ForeignKey(UnderwritingAgreement, null=False, blank=False,
        on_delete=models.PROTECT,  # Don't allow deletion of an agreement that we've partially fulfilled.
        help_text="The associated agreement.")

    when_read = models.DateTimeField(default=datetime.now,
        help_text="The date & time the spot was read on-air.")

