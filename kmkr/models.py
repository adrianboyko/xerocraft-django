
# Standard
from datetime import date

# Third-party
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone

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


class OnAirPersonalitySocialMedia (models.Model):

    personality = models.ForeignKey(OnAirPersonality, null=False, blank=False,
        on_delete=models.CASCADE,  # If we're getting rid of the personality, we don't need their social media info.
        help_text="The on air personality associated with this social media account.")

    social_media = models.URLField(null=False, blank=False,
        help_text="URL for the personality's social media account.")

    class Meta:
        verbose_name = "On Air Personality's Social Media"
        verbose_name_plural = "On Air Personality's Social Media"


class Show (models.Model):

    title = models.CharField(max_length=80,
        help_text="The name of this show.")

    description = models.TextField(max_length=2048,
        help_text="A description of the show for public consumption.")

    hosts = models.ManyToManyField(OnAirPersonality,
        help_text="Host(s) of the show.")

    active = models.BooleanField(default=True,
        help_text="Checked if this show is still active.")

    @property
    def days_of_week_str(self) -> str:
        return abutils.time.days_of_week_str(self)

    def __str__(self) -> str:
        return self.title


class ShowTime(models.Model):

    show = models.ForeignKey(Show, null=False, blank=False,
        on_delete=models.CASCADE,
        help_text="The show in question.")

    start_time = models.TimeField(null=False, blank=False,
        help_text="The time at which the show begins.")

    minute_duration = models.IntegerField(null=False, blank=False,
        help_text="The duration of the show in MINUTES.")

    # Weekday of month:
    first = models.BooleanField(default=False, verbose_name="1st")
    second = models.BooleanField(default=False, verbose_name="2nd")
    third = models.BooleanField(default=False, verbose_name="3rd")
    fourth = models.BooleanField(default=False, verbose_name="4th")
    every = models.BooleanField(default=True)

    # Day of week:
    sundays = models.BooleanField(default=False, verbose_name="Sun")
    mondays = models.BooleanField(default=False, verbose_name="Mon")
    tuesdays = models.BooleanField(default=False, verbose_name="Tue")
    wednesdays = models.BooleanField(default=False, verbose_name="Wed")
    thursdays = models.BooleanField(default=False, verbose_name="Thu")
    fridays = models.BooleanField(default=False, verbose_name="Fri")
    saturdays = models.BooleanField(default=False, verbose_name="Sat")


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

    track_id = models.IntegerField(blank=True, null=True,
        help_text="The ID of the associated track on Radio DJ.")

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


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# WHAT'S PLAYING
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Track (models.Model):

    duration = models.DurationField(blank=False, null=False,
        help_text="The expected duration of the item.")

    TITLE_MAX_LENGTH = 128
    title = models.CharField(max_length=TITLE_MAX_LENGTH, blank=False, null=False,
        help_text="The title of the item.")

    ARTIST_MAX_LENGTH = 128
    artist = models.CharField(max_length=ARTIST_MAX_LENGTH, blank=False, null=False,
        help_text="The artist/dj/etc featured in this item.")

    radiodj_id = models.IntegerField(blank=False, null=False, unique=True,
        help_text="The track ID of the item in the Radio DJ database.")

    TYPE_MUSIC = 0
    TYPE_JINGLE = 1
    TYPE_SWEEPER = 2
    TYPE_VOICEOVER = 3
    TYPE_COMMERCIAL = 4
    TYPE_ISTREAM = 5
    TYPE_OTHER = 6
    TYPE_VDF = 7
    TYPE_REQUEST = 8
    TYPE_NEWS = 9
    TYPE_PLAYLIST_EVENT = 10
    TYPE_FILE_BY_DATE = 11
    TYPE_NEWEST_FROM_FOLDER = 12
    TYPE_CHOICES = [
        (TYPE_MUSIC, "Music"),
        (TYPE_JINGLE, "Jingle"),
        (TYPE_SWEEPER, "Sweeper"),
        (TYPE_VOICEOVER, "Voiceover"),
        (TYPE_COMMERCIAL, "Commercial"),
        (TYPE_ISTREAM, "Internet Stream"),
        (TYPE_OTHER, "Other"),
        (TYPE_VDF, "Variable Duration File"),
        (TYPE_REQUEST, "Request"),
        (TYPE_NEWS, "News"),
        (TYPE_PLAYLIST_EVENT, "Playlist Event"),
        (TYPE_FILE_BY_DATE, "File By Date"),
        (TYPE_NEWEST_FROM_FOLDER, "Newest From Folder"),
    ]
    track_type = models.IntegerField(blank=False, null=False,
        choices=TYPE_CHOICES,
        help_text="The type of the item in the Radio DJ database.")

    def __str__(self) -> str:
        return '"{}" by {}'.format(self.title, self.artist)


class PlayLogEntry (models.Model):

    start = models.DateTimeField(blank=False, null=False,
        default=timezone.now,
        help_text="The date & time that airing of item began.")

    track = models.ForeignKey(Track, null=False, blank=False,
        on_delete=models.PROTECT,  # Don't allow deletion of track if it has been aired.
        help_text="The track which was aired.")

    class Meta:
        verbose_name = "Play Log Entry"
        verbose_name_plural = "Play Log Entries"


class Rating (models.Model):

    what = models.ForeignKey(PlayLogEntry, blank=False, null=False,
        on_delete=models.CASCADE,
        help_text="What was rated.")

    who = models.ForeignKey(Member, blank=False, null=False,
        on_delete=models.CASCADE,
        help_text="Person who rated.")

    RATE_TWO_THUMBS_UP = 2
    RATE_ONE_THUMB_UP = 1
    RATE_NEUTRAL = 0
    RATE_ONE_THUMB_DOWN = -1
    RATE_TWO_THUMBS_DOWN = -2
    RATE_CHOICES = [
        (RATE_TWO_THUMBS_UP, "Two thumbs up"),
        (RATE_ONE_THUMB_UP, "One thumb up"),
        (RATE_NEUTRAL, "Neutral"),
        (RATE_ONE_THUMB_DOWN, "One thumb down"),
        (RATE_TWO_THUMBS_DOWN, "Two thumbs down"),
    ]
    rating = models.IntegerField(blank=False, null=False,
        choices=RATE_CHOICES,
        help_text="The rating")

    class Meta:
        unique_together = ['what', 'who']