
# Standard

# Third-Party
from django.contrib import admin
from django.db.models import Sum, Count, F
from django.utils import timezone
from reversion.admin import VersionAdmin

# Local
from kmkr.models import (
    Show, ShowTime, Episode, EpisodeTrack, Broadcast,
    UnderwritingQuote, UnderwritingDeal,
    UnderwritingBroadcastLog, UnderwritingBroadcastSchedule,
    OnAirPersonality,
    OnAirPersonalitySocialMedia,
    PlayLogEntry, Track, Rating
)
from books.admin import Sellable


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ON-AIR PERSONALITY
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(OnAirPersonality)
class OnAirPersonalityAdmin(VersionAdmin):

    class SocialMedia_Inline(admin.TabularInline):
        model = OnAirPersonalitySocialMedia
        model._meta.verbose_name = "Social Media Acct"
        extra = 0
        raw_id_fields = ['personality']

    list_display = ['pk', 'member', 'moniker', 'active']
    list_display_links = ['pk', 'member',]
    raw_id_fields = ['member']
    list_filter = ['active']
    inlines = [SocialMedia_Inline]

    class Media:
        css = {
            # This hides "denormalized object descs", to use Wojciech's term.
            "all": ("abutils/admin-tabular-inline.css",)
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# SHOW
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(Show)
class ShowAdmin(VersionAdmin):

    list_filter = ['active']

    def hosts_fmt(self, show: Show):
        result = map(
            lambda h: h.moniker,
            show.hosts.all()
        )
        return list(result)
    hosts_fmt.short_description = 'host(s)'

    list_display = ['id', 'title', 'duration', 'hosts_fmt', 'active']

    list_display_links = ['id', 'title']

    fields = ['title', 'duration', 'description', 'active']

    search_fields = ['title', 'description']

    class Host_Inline(admin.TabularInline):
        model = Show.hosts.through
        model._meta.verbose_name = "Host"
        model._meta.verbose_name_plural = "Hosts"
        extra = 0
        raw_id_fields = ['onairpersonality']

    class ShowTime_Inline(admin.TabularInline):
        model = ShowTime
        extra = 0
        raw_id_fields = ['show']

    inlines = [Host_Inline, ShowTime_Inline]

    class Media:
        css = {
            # This hides "denormalized object descs", to use Wojciech's term.
            "all": ("abutils/admin-tabular-inline.css",)
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# UNDERWRITING SPOTS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(UnderwritingQuote)
class UnderwritingQuoteAdmin(VersionAdmin):

    list_display = [
        'pk',
        'active',
        'prepared_for',
        'date_prepared',
        'quoted_price',
        'spot_seconds',
        'track_id'
    ]

    list_display_links = ['pk']

    fields = [
        'active',
        ('prepared_for', 'date_prepared'),
        'quoted_price',
        'spot_seconds',
        'track_id',
        'script'
    ]

    class UnderwritingBroadcastSchedule_Inline(admin.TabularInline):
        model = UnderwritingBroadcastSchedule
        extra = 0
        raw_id_fields = ['agreement']

    inlines = [UnderwritingBroadcastSchedule_Inline]

    date_hierarchy = 'date_prepared'

    list_filter = ['active']

    search_fields = [
        'prepared_for',
    ]

    class Media:
        css = {
            "all": (
                "abutils/admin-tabular-inline.css",  # This hides "denormalized object descs", to use Wojciech's term.
                "kmkr/kmkr.css"
            )
        }
        js = ["kmkr/kmkr.js"]


@admin.register(UnderwritingDeal)
class UnderwritingDealAdmin(VersionAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = [
        'pk',
        'underwriter_name',
        'start_date',
        'end_date',
        'quote_link',
        'sale_link',
    ]

    fields = [
        'underwriter_name',
        'start_date',
        'end_date',
        'quote_link',
        'sale_link',
    ]

    readonly_fields = ['sale_link', 'quote_link', 'underwriter_name']

    search_fields = [
        'sale__payer_name',
    ]

    class DateRangeFilter(admin.SimpleListFilter):
        title = "delivery range"
        parameter_name = "range"

        def lookups(self, request, model_admin):
            return (
                ('past', "Past"),
                ('current', "Current"),
                ('future', "Future"),
            )

        def queryset(self, request, queryset):
            d = timezone.now().date()
            if self.value() == 'past':
                return queryset.filter(end_date__lt=d)
            if self.value() == 'future':
                return queryset.filter(start_date__gt=d)
            if self.value() == 'current':
                return queryset.filter(start_date__lte=d, end_date__gte=d)

    list_filter = [DateRangeFilter]

    class UnderwritingBroadcastLog_Inline(admin.TabularInline):
        model = UnderwritingBroadcastLog
        extra = 0
        raw_id_fields = []
        readonly_fields = ['schedule']
        fields = ['schedule', 'when_read']
        ordering = ['when_read']

    inlines = [UnderwritingBroadcastLog_Inline]

    class Media:
        css = {
            "all": (
                "abutils/admin-tabular-inline.css",  # This hides synthesized obj descriptions
                "kmkr/kmkr.css"
            )
        }
        js = ["kmkr/kmkr.js"]  # This modifies layout of DateTime widget.


@Sellable(UnderwritingDeal)  # Line-Item Inline for SaleAdmin in Books app.
class UnderwritingDeal_Inline(admin.StackedInline):
    fields = [
        'sale_price',
        ('start_date', 'end_date'),
        'quote'
    ]

    extra = 0

    raw_id_fields = ['quote']


# TODO: Comment out. Only for development/debugging.
# @admin.register(UnderwritingBroadcastLog)
# class UnderwritingBroadcastLogAdmin(VersionAdmin):
#     pass


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# PLAY LOG & TRACKS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):

    list_filter = ['track_type']

    search_fields = ['title', 'artist']

    list_display = [
        'pk',
        'title',
        'artist',
        'radiodj_id',
        'track_type'
    ]


@admin.register(PlayLogEntry)
class PlayLogEntryAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        qs = super(PlayLogEntryAdmin, self).get_queryset(request)
        return qs.annotate(Sum('rating__rating')).annotate(Count('rating'))

    def rating(self, ple: PlayLogEntry):
        return ple.rating__rating__sum

    def votes(self, ple: PlayLogEntry) -> str:
        cnt = ple.rating__count
        return "-" if cnt == 0 else str(cnt)

    def one_thumb_up(self, ple: PlayLogEntry) -> int:
        return ple.rating_set.filter(rating=Rating.RATE_ONE_THUMB_UP).count()

    def one_thumb_down(self, ple: PlayLogEntry) -> int:
        return ple.rating_set.filter(rating=Rating.RATE_ONE_THUMB_DOWN).count()

    list_filter = ['track__track_type']

    search_fields = [
        'track__title',
        'track__artist',
        'non_library_track__title',
        'non_library_track__artist',
    ]

    date_hierarchy = 'start'

    list_display = [
        'pk',
        'start',
        'artist',
        'title',
        'rating',
        'votes',
    ]

    raw_id_fields = ['track', 'non_library_track']

    class Rating_Inline(admin.TabularInline):
        model = Rating
        extra = 0
        raw_id_fields = ['who']

    inlines = [Rating_Inline]


@admin.register(EpisodeTrack)
class EpisodeTrackAdmin(admin.ModelAdmin):

    list_filter = ['episode__show']

    date_hierarchy = 'episode__first_broadcast'

    list_display = [
        'pk',
        'episode',
        'sequence',
        'artist',
        'title',
        'duration',
    ]

    raw_id_fields = ['episode']


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):

    list_display = [
        'pk',
        'show',
        'first_broadcast',
        'title',
    ]

    date_hierarchy = 'first_broadcast'

    raw_id_fields = ['show']

    class Playlist_Inline(admin.TabularInline):
        model = EpisodeTrack
        extra = 0
        raw_id_fields = []

    inlines = [Playlist_Inline]

    list_filter = ['show']

    class Media:
        css = {
            # This hides synthesized obj descriptions
            "all": ("abutils/admin-tabular-inline.css",)
        }

@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):

    list_display = [
        'pk',
        'episode',
        'date',
        'host_checked_in',
        'type'
    ]

    raw_id_fields = ['episode']
