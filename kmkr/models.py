
# Standard
from datetime import date

# Third-party
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

# Local
from books.models import SaleLineItem
from members.models import Member
import abutils.time


class OnAirPersonality (models.Model):

    member = models.ForeignKey(Member, null=False, blank=False,
        on_delete=models.PROTECT,  # Don't allow deletion of member.
        help_text="The member who is authorized to be on air.")

    moniker = models.CharField(max_length=40,
        help_text="Moniker/nickname such as 'The Vinyl Wizard'.")

    bio = models.TextField(max_length=2048,
        help_text="Biographical info for public consumption.")

    active = models.BooleanField(default=True,
        help_text="Checked if this person is still active.")

    def __str__(self) -> str:
        return "{} aka '{}'".format(self.member.username, self.moniker)

    class Meta:
        verbose_name = "On Air Personality"
        verbose_name_plural = "On Air Personalities"


class Show (models.Model):

    title = models.CharField(max_length=80,
        help_text="A short description/name for the task.")

    description = models.TextField(max_length=2048,
        help_text="A description of the show for public consumption.")

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
        help_text="Host(s) of the show.")

    active = models.BooleanField(default=True,
        help_text="Checked if this show is still active.")

    @property
    def days_of_week_str(self) -> str:
        return abutils.time.days_of_week_str(self)

    def __str__(self) -> str:
        return self.title


class UnderwritingSpots (SaleLineItem):

    holds_donation = models.ForeignKey(Member, null=True, blank=True,
        on_delete=models.PROTECT,
        help_text="Who currently has the donation in hand. Blank if already deposited or submitted to treasurer.")

    start_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="The first day on which a spot can run.")

    end_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="The last day on which a spot can run.")

    spot_seconds = models.IntegerField(null=False, blank=False,
        validators=[MinValueValidator(0)],
        help_text="The length of each spot in seconds.")

    SLOT_DAY    = "DAY"
    SLOT_DRIVE  = "DRV"
    SLOT_SHOW   = "SHW"
    SLOT_CUSTOM = "CST"
    SLOT_CHOICES = [
        (SLOT_DAY,    "Daytime"),
        (SLOT_DRIVE,  "Drivetime"),
        (SLOT_SHOW,   "Specific Show(s)"),
        (SLOT_CUSTOM, "Custom Time")
    ]
    slot = models.CharField(max_length=3, choices=SLOT_CHOICES, null=False, blank=False,
        help_text="The time slot during which the spot(s) can air.")

    specific_shows = models.ManyToManyField(Show, blank=True,
        help_text="If spot(s) MUST run during some specific show(s), select them.")

    title = models.CharField(max_length=80,
        help_text="The name of the audio file on Radio DJ.")

    script = models.TextField(max_length=2048, blank=False,
        help_text="The text to read on-air.")

    custom_details = models.TextField(max_length=1024, blank=True,
        help_text="Specify details if slot is CUSTOM.")

    def clean(self) -> None:

        if self.start_date >= self.end_date:
            raise ValidationError("End date must be later than start date.")

        if self.slot == self.SLOT_CUSTOM and len(self.custom_details.strip())==0:
            raise ValidationError("Instructions must be specified if slot is 'custom'")

    def dbcheck(self):

        if self.slot == self.SLOT_SHOW and len(self.specific_shows.count())==0:
            raise ValidationError("At least one show must be specified if slot is 'speciic show(s)'")


    class Meta:
        verbose_name = "Underwriting Spots"
        verbose_name_plural = "Underwriting Spots"


class UnderwritingLogEntry (models.Model):

    spec = models.ForeignKey(UnderwritingSpots, null=False, blank=False,
        on_delete=models.PROTECT,  # Don't allow deletion of an agreement that we've partially fulfilled.
        help_text="The associated agreement.")

    when_read = models.DateTimeField(blank=False,
        help_text="The date & time the spot was read on-air.")

    class Meta:
        verbose_name = "Underwriting Log Entry"
        verbose_name_plural = "Underwriting Log Entries"

