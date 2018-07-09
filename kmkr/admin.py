
# Standard

# Third-Party
from django.contrib import admin
from django.db.models import Sum, Count
from reversion.admin import VersionAdmin

# Local
from kmkr.models import (
    Show, ShowTime,
    UnderwritingSpots,
    UnderwritingLogEntry,
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

    list_display = ['id', 'title', 'hosts_fmt', 'active']

    list_display_links = ['id', 'title']

    fields = ['title', 'description', 'active']

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

@admin.register(UnderwritingSpots)
class UnderwritingSpotsAdmin(VersionAdmin):

    def underwriter(self, obj: UnderwritingSpots) -> str:
        return obj.sale.payer_name

    def num_spots(self, obj: UnderwritingSpots) -> str:
        return str(obj.qty_sold)

    def spot_price(self, obj: UnderwritingSpots) -> str:
        return str(obj.sale_price)

    def transaction_number(self, obj: UnderwritingSpots) -> str:
        return str(obj.sale.pk)

    raw_id_fields = ['holds_donation']

    list_display = [
        'pk',
        'underwriter',
        'sale_price', 'qty_sold',
        'start_date', 'end_date',
        'spot_seconds',
        'slot',
        'holds_donation'
    ]

    list_display_links = ['pk']

    fields = [
        ('transaction_number', 'underwriter'),
        'holds_donation',
        ('sale_price', 'qty_sold'),
        ('start_date', 'end_date'),
        ('spot_seconds', 'slot', 'track_id'),
        ('script', 'custom_details')
    ]

    class SpecificShows_Inline(admin.TabularInline):
        model = UnderwritingSpots.specific_shows.through
        model._meta.verbose_name = "Specific Show"
        model._meta.verbose_name_plural = "Specific Shows"
        extra = 0

    class UnderwritingLog_Inline(admin.TabularInline):
        model = UnderwritingLogEntry
        model._meta.verbose_name = "Log Entry"
        model._meta.verbose_name_plural = "Log Entries"
        extra = 0

    inlines = [SpecificShows_Inline, UnderwritingLog_Inline]

    readonly_fields = ['transaction_number', 'underwriter']

    list_filter = ['slot']

    search_fields = [
        'sale__payer_name',
        'holds_donation__auth_user__first_name',
        'holds_donation__auth_user__last_name',
        'holds_donation__auth_user__username'
    ]

    def has_add_permission(self, request):
        return False
        # Add users instead, which drives creation of a Member.

    def has_delete_permission(self, request, obj=None):
        return False
        # Deactivate users instead.

    class Media:
        css = {
            "all": (
                "abutils/admin-tabular-inline.css", # This hides "denormalized object descs", to use Wojciech's term.
                "kmkr/kmkr.css"
            )
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Line-Item Inlines for SaleAdmin in Books app.
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@Sellable(UnderwritingSpots)
class UnderwritingSpots_LineItem(admin.StackedInline):
    fields = [
        'holds_donation',
        ('sale_price', 'qty_sold'),
        ('start_date', 'end_date'),
        'spot_seconds',
        'slot',
        'script',
        'specific_shows',
        'custom_details'
    ]
    extra = 0
    raw_id_fields = ['holds_donation']


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

    search_fields = ['track__title', 'track__artist']

    date_hierarchy = 'start'

    list_display = [
        'pk',
        'start',
        'track',
        'rating',
        'votes',
    ]

    raw_id_fields = ['track']

    class Rating_Inline(admin.TabularInline):
        model = Rating
        extra = 0
        raw_id_fields = ['who']

    inlines = [Rating_Inline]