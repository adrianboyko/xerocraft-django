
# Standard
from datetime import date, time, datetime, timedelta
from typing import Optional, Tuple
from logging import getLogger

# Third-party
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.html import format_html

# Local
from books.models import SaleLineItem, Entity
from members.models import Member
import abutils.time as abtime
from abutils.models import get_url_str

logger = getLogger("kmkr")
oneday = timedelta(days=1)


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
        verbose_name = "On air personality"
        verbose_name_plural = "On air personalities"


class OnAirPersonalitySocialMedia (models.Model):

    personality = models.ForeignKey(OnAirPersonality, null=False, blank=False,
        on_delete=models.CASCADE,  # If we're getting rid of the personality, we don't need their social media info.
        help_text="The on air personality associated with this social media account.")

    social_media = models.URLField(null=False, blank=False,
        help_text="URL for the personality's social media account.")

    class Meta:
        verbose_name = "On Air Personality's Social Acct"


class Show (models.Model):

    title = models.CharField(max_length=80,
        help_text="The name of this show.")

    description = models.TextField(max_length=2048, null=False, blank=False,
        help_text="A description of the show for public consumption.")

    hosts = models.ManyToManyField(OnAirPersonality,
        help_text="Host(s) of the show.")

    duration = models.DurationField(null=False, blank=False,
        default=timedelta(minutes=60),
        help_text="The duration of the show.")

    active = models.BooleanField(default=True,
        help_text="Checked if this show is still active.")

    @property
    def days_of_week_str(self) -> str:
        return abtime.days_of_week_str(self)

    def __str__(self) -> str:
        return self.title

    def is_in_progress(self) -> bool:
        lt = timezone.localtime(timezone.now())
        return any(x.covers(lt) for x in self.showtime_set.all())

    @classmethod
    def current_show(cls) -> Optional['Show']:
        for show in Show.objects.all():
            if show.is_in_progress():
              return show
        return None

    def current_showtime(self) -> Optional['ShowTime']:
        lt = timezone.localtime(timezone.now())
        for showtime in self.showtime_set.all():  # type: ShowTime
            if showtime.covers(lt):
                return showtime
        return None


class ShowTime(models.Model):

    show = models.ForeignKey(Show, null=False, blank=False,
        on_delete=models.CASCADE,
        help_text="The show in question.")

    start_time = models.TimeField(null=False, blank=False,
        help_text="The time at which the show begins.")

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

    PRODUCTION_LIVE = "LIV"
    PRODUCTION_PRERECORDED = "PRE"
    PRODUCTION_CHOICES = [
        (PRODUCTION_LIVE, "Live"),
        (PRODUCTION_PRERECORDED, "Prerecorded"),
    ]
    production_method = models.CharField(max_length=3, choices=PRODUCTION_CHOICES,
        null=False, blank=False,
        help_text="Default production method for this show time.")

    # Some dynamic code (in other modules) requires these aliases:
    @property
    def sunday(self) -> bool: return self.sundays
    @property
    def monday(self) -> bool: return self.mondays
    @property
    def tuesday(self) -> bool: return self.tuesdays
    @property
    def wednesday(self) -> bool: return self.wednesdays
    @property
    def thursday(self) -> bool: return self.thursdays
    @property
    def friday(self) -> bool: return self.fridays
    @property
    def saturday(self) -> bool: return self.saturdays

    def covers(self, dt: datetime) -> bool:
        day_match = abtime.matches_weekday_of_month_pattern(self, dt.date())
        time_match = abtime.time_in_timespan(
            dt.time(),
            self.start_time,
            self.show.duration
        )
        return True if day_match and time_match else False


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Underwriting
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class UnderwritingQuote(models.Model):

    prepared_for = models.ForeignKey(Entity, null=False, blank=False,
        on_delete=models.CASCADE,
        help_text="The business/organization for whom this quote was prepared.")

    date_prepared = models.DateField(null=False, blank=False, default=date.today,
        help_text="The date on which this quote was prepared.")

    active = models.BooleanField(default=True,
        help_text="Checked if this quote is still being offered to the underwriter.")

    quoted_price = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The quoted price.")

    spot_seconds = models.IntegerField(null=False, blank=False,
        validators=[MinValueValidator(0)],
        help_text="The length of each spot in seconds.")

    track_id = models.IntegerField(blank=True, null=True,
        help_text="The ID of the associated track on Radio DJ.")

    script = models.TextField(max_length=2048, blank=False,
        help_text="The text to read on-air.")

    def __str__(self):
        return "{} quote for {}".format(self.date_prepared, self.prepared_for.name)

    def best_schedule_match(self, dt: datetime) -> 'UnderwritingBroadcastSchedule':
        dt = timezone.localtime(dt)  # Schedules are specified in local days/times, so make sure dt is local.
        dt_weekday = dt.weekday()
        min_diff = None  # type: Optional[float]
        best_match = None  # type: Optional[UnderwritingBroadcastSchedule]
        for sched in self.underwritingbroadcastschedule_set.all():  # type: UnderwritingBroadcastSchedule
            diff = None  # type: Optional[float]
            for n in [-1, 0, 1]:  # prev weekday, same weekday, next weekday
                if sched.covers_weekday((dt_weekday-n) % 7):
                    # The schedule covers the previous weekday BEFORE dt's weekday.
                    sched_dt = (dt+n*oneday).replace(hour=sched.time.hour, minute=sched.time.minute)
                    diff = abs((dt-sched_dt).total_seconds())
                    if min_diff is None or (diff < min_diff):
                        min_diff = diff
                        best_match = sched
        return best_match


class UnderwritingBroadcastSchedule (models.Model):  # TODO: Rename to UnderwritingScheduleLineItem?

    # TODO: Rename agreement -> quote
    agreement = models.ForeignKey(UnderwritingQuote, null=False, blank=False,
        on_delete=models.CASCADE,
        help_text="The associated quote.")
    @property
    def quote(self) -> UnderwritingQuote:
        return self.agreement

    num_spots = models.IntegerField(null=False, blank=False,
        validators=[MinValueValidator(0)],
        help_text="The number of spots to broadcast in this time slot.")

    time = models.TimeField(null=False, blank=False,
        help_text="The time to broadcast the underwriter's spot.")

    # Day of week:
    sundays = models.BooleanField(default=False, verbose_name="Sun")
    mondays = models.BooleanField(default=False, verbose_name="Mon")
    tuesdays = models.BooleanField(default=False, verbose_name="Tue")
    wednesdays = models.BooleanField(default=False, verbose_name="Wed")
    thursdays = models.BooleanField(default=False, verbose_name="Thu")
    fridays = models.BooleanField(default=False, verbose_name="Fri")
    saturdays = models.BooleanField(default=False, verbose_name="Sat")

    # Some dynamic code (in other modules) requires these aliases:
    def first(self) -> bool: return False
    @property
    def second(self) -> bool: return False
    @property
    def third(self) -> bool: return False
    @property
    def fourth(self) -> bool: return False
    @property
    def every(self) -> bool: return True

    def covers_weekday(self, wd: int):
        return (wd==0 and self.mondays) \
         or (wd==1 and self.tuesdays) \
         or (wd==2 and self.wednesdays) \
         or (wd==3 and self.thursdays) \
         or (wd==4 and self.fridays) \
         or (wd==5 and self.saturdays) \
         or (wd==6 and self.sundays)

    def __str__(self):
        return "{} @ {}".format(abtime.days_of_week_str(self), self.time)


# TODO: @register_journaler()  ... Class must inherit from Journaler.
class UnderwritingDeal(SaleLineItem):

    quote = models.ForeignKey(UnderwritingQuote, null=False, blank=False,
        on_delete=models.PROTECT,
        help_text="The associated quote, which contains the terms of this dea.")

    start_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="Underwriter's preference for first day on which a spot will run.")

    end_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="Underwriter's preference for last day on which a spot will run.")

    @property
    def underwriter_name(self):
        return self.sale.payer_str

    @property
    def quote_link(self):
        url_str = get_url_str(self.quote)
        return format_html("<a href='{}'>{}</a>", url_str, self.quote)

    @property
    def is_fully_delivered(self) -> bool:
        return False  # TODO: IMPLEMENT ME

    def __str__(self) -> str:
        return "{} deal dated {}".format(self.sale.payer_str, self.sale.sale_date)

    def clean(self) -> None:
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be later than start date.")


class UnderwritingBroadcastLog (models.Model):

    deal = models.ForeignKey(UnderwritingDeal, null=False, blank=False,
        on_delete=models.PROTECT,  # Don't allow deletion of a sale line item if we're partially delivered it.
        help_text="The associated sale line item.")

    # NOTE: Each schedule line item needs to be independently satisfied.
    schedule = models.ForeignKey(UnderwritingBroadcastSchedule, null=False, blank=False,
        on_delete=models.PROTECT,
        help_text="The associated schedule the quote.")

    when_read = models.DateTimeField(blank=False,
        help_text="The date & time the spot was read on-air.")

    class Meta:
        unique_together = ['deal', 'when_read']


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

    class Meta:
        verbose_name = "Track in library"
        verbose_name_plural = "Tracks in library"


class Episode(models.Model):

    show = models.ForeignKey(Show, blank=True, null=True,
        on_delete=models.SET_NULL,
        help_text="Specify the show of which this is an episode.")

    first_broadcast = models.DateField(blank=True, null=True,
        help_text="The date of the first broadcast of this episode.")

    # Might as well reuse TITLE_MAX_LENGTH here.
    title = models.CharField(max_length=Track.TITLE_MAX_LENGTH, blank=True, null=False, default="",
        help_text="The (optional) title of this episode.")

    def __str__(self):
        return "'{}' episode 1st aired {}".format(self.show, self.first_broadcast)

    class Meta:
        unique_together = ['show', 'first_broadcast']


class Broadcast(models.Model):
    """
    Represents a broadcast of an episode of a show. For live episodes, this is used to verify that the host
    actually showed up and that the official play log should ignore RadioDJ for the duration of the show.
    Also the grouping mechanism for ManualPlayListEntries.
    """

    episode = models.ForeignKey(Episode, blank=False, null=False,
        on_delete=models.PROTECT,
        help_text="The episode that will be broadcast.")

    date = models.DateField(blank=False, null=False,
        help_text="The date of the broadcast.")

    host_checked_in = models.TimeField(blank=True, null=True,
        help_text="Specify for original live broadcast, but not for repeat broadcasts.")

    TYPE_FIRST_RUN = "1ST"  # These can be either live or recorded
    TYPE_REPEAT = "RPT"  # These are always recorded.
    TYPE_CHOICES = [
        (TYPE_FIRST_RUN, "First Broadcast"),
        (TYPE_REPEAT, "Repeat Broadcast"),
    ]
    type = models.CharField(max_length=3, choices=TYPE_CHOICES,
        null=False, blank=False,
        help_text="Is this an original or repeat broadcast?")

    def __str__(self):
        return "{} on {}".format(self.episode, self.date)

    def clean(self):
        if self.host_checked_in is not None and self.type != self.TYPE_FIRST_RUN:
            raise ValidationError("Host doesn't need to check in if broadcast is not live.")

    class Meta:
        unique_together = ['episode', 'date', 'type']
        verbose_name = "Episode broadcast"


# Since this table is scratch space, all metadata fields including duration are strings. Fields like
# duration will be changed into more precise types when data migrates from this table to PlayLogEntry.
class EpisodeTrack(models.Model):
    """
      A place for DJs to manually enter the music associated with an episode.
      They can do this before or during the show, using the "DJ Ops" app.
      Information staged here will transition into PlayLogEntry
      as the DJ indicates that they are being played.
    """

    episode = models.ForeignKey(Episode, blank=False, null=False,
        on_delete=models.CASCADE,
        help_text="The associated episode.")

    sequence = models.IntegerField(blank=False, null=False,
        help_text="The position of the track in the playlist.")

    artist = models.CharField(max_length=Track.ARTIST_MAX_LENGTH, blank=True, null=False, default="",
        help_text="The artist who performed the track.")

    title = models.CharField(max_length=Track.TITLE_MAX_LENGTH, blank=True, null=False, default="",
        help_text="The title of the track.")

    duration = models.CharField(max_length=5, blank=True, null=False, default="",
        help_text="The duration of the track as MM:SS.")

    track_broadcast = models.ForeignKey('PlayLogEntry', blank=True, null=True,
        on_delete=models.PROTECT,
        help_text="The record of this track's broadcast, if it was broadcast.")

    def __str__(self) -> str:
        return '"{}" by {}'.format(self.title, self.artist)

    class Meta:
        unique_together = ['episode', 'sequence']
        verbose_name = "Track for episode"
        verbose_name_plural = "Tracks for episode"


# TODO: Rename PlayLogEntry to TrackBroadcast
class PlayLogEntry (models.Model):
    """This is the official record of what played on-air."""

    start = models.DateTimeField(blank=False, null=False,
        help_text="The exact datetime (within a few seconds) that play began.")

    # TODO: Rename track to library_track
    track = models.ForeignKey(Track, null=True, blank=True,
        on_delete=models.PROTECT,  # Don't allow deletion of track if it has been aired.
        help_text="The library track which was played.")

    non_library_track = models.ForeignKey(EpisodeTrack, null=True, blank=True,
        on_delete=models.PROTECT,  # Don't allow deletion of track if it has been aired.
        help_text="The NON-library track which was played.")

    def clean(self):
        if self.track is not None and self.non_library_track is not None:
            raise ValidationError("Specify ONE of library track or NON-library track, not both.")
        if self.track is None and self.non_library_track is None:
            raise ValidationError("You must specify ONE of library track or NON-library track.")

    @property
    def artist(self) -> str:
        if self.track is not None:
            return self.track.artist
        elif self.non_library_track is not None:
            return self.non_library_track.artist
        else:
            logger.error("Track broadcast #{} has NULL track and non_libary_track.".format(self.id))
            return "uknown"

    @property
    def title(self) -> str:
        if self.track is not None:
            return self.track.title
        elif self.non_library_track is not None:
            return self.non_library_track.title
        else:
            logger.error("Track broadcast #{} has NULL track and non_libary_track.".format(self.id))
            return "uknown"

    @property
    def duration(self) -> timedelta :
        if self.track is not None:
            return self.track.duration
        elif self.non_library_track is not None:
            dur_str = ""
            try:
                # REVIEW: Is returning 0 for unspecified and unparsable the best approach?
                dur_str = self.non_library_track.duration
                if len(dur_str.strip()) == 0:
                    return timedelta(seconds=0)
                parts = dur_str.split(":")
                return timedelta(seconds=int(parts[0])*60 + int(parts[1]))
            except:
                logger.error("Track broadcast #{}, can't parse duration: {}".format(self.id, dur_str))
                return timedelta(seconds=0)
        else:
            logger.error("Track broadcast #{} has NULL track and non_libary_track.".format(self.id))
            return timedelta(seconds=0)

    class Meta:
        verbose_name = "Track broadcast"
        verbose_name_plural = "Tracks broadcast"


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