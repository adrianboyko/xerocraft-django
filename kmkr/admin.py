
# Standard

# Third-Party
from django.contrib import admin
from reversion.admin import VersionAdmin

# Local
from kmkr.models import (
    Show,
    UnderwritingSpots,
    UnderwritingLogEntry,
    OnAirPersonality,
)
from books.admin import Sellable


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ON-AIR PERSONALITY
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(OnAirPersonality)
class OnAirPersonalityAdmin(VersionAdmin):
    list_display = ['pk', 'member', 'moniker', 'active']
    list_display_links = ['pk', 'member',]
    raw_id_fields = ['member']
    list_filter = ['active']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# SHOW
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(Show)
class ShowAdmin(VersionAdmin):

    class Host_Inline(admin.TabularInline):
        model = Show.hosts.through
        model._meta.verbose_name = "Host"
        model._meta.verbose_name_plural = "Hosts"
        extra = 0
        raw_id_fields = ['onairpersonality']

    def days(self, obj:Show)->str: return obj.days_of_week_str

    def mins(self, obj:Show)->str: return str(obj.minute_duration)

    list_filter = ['active']

    list_display = ['id', 'title', 'days', 'start_time', 'mins', 'active']

    list_display_links = ['id', 'title']

    fieldsets = [
        ("BASICS",
            {'fields': ['title', 'description', 'active']}),
        ("SCHEDULE",
            {'fields': [
                ('mondays', 'tuesdays', 'wednesdays', 'thursdays', 'fridays', 'saturdays', 'sundays'),
                'start_time',
                'minute_duration',
        ]})
    ]

    search_fields = ['title', 'description']

    inlines = [Host_Inline]

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
        ('spot_seconds', 'slot'),
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


