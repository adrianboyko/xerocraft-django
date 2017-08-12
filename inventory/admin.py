
# Standard
import math

# Third Party
from django.contrib import admin
from django.db.models import F, DecimalField
from django.forms import NumberInput
from django.utils.html import format_html
from reversion.admin import VersionAdmin

# Local
from inventory.models import (
    PermitScan, ParkingPermitPayment, ParkingPermit,
    Location, Shop, Tool,
    ConsumableToStock
)


class ParkingPermitPaymentInline(admin.TabularInline):
    model = ParkingPermitPayment
    extra = 0

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)
        }


class PermitScanInline(admin.TabularInline):
    model = PermitScan
    extra = 0
    raw_id_fields = ['who']

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)
        }


@admin.register(ParkingPermit)
class ParkingPermitAdmin(VersionAdmin):
    list_display = [
        'pk',
        'short_desc',
        'owner',
        'ok_to_move',
        'is_in_inventoried_space',
        'price_per_period',
        'billing_period',
    ]
    list_display_links = ['pk', 'short_desc']
    fields = [
        ('short_desc', 'created'),
        ('owner', 'approving_member'),
        'location',
        'ok_to_move',
        'is_in_inventoried_space',
        ('price_per_period', 'billing_period'),
    ]
    readonly_fields = ['created']
    inlines = [ParkingPermitPaymentInline, PermitScanInline]
    raw_id_fields = ['owner', 'approving_member', 'location']

    search_fields = [
        '^owner__auth_user__first_name',
        '^owner__auth_user__last_name',
        '^owner__auth_user__username',
        '^owner__auth_user__email',
    ]


@admin.register(PermitScan)
class PermitScanAdmin(VersionAdmin):
    list_display = ['pk', 'when', 'permit', 'where']
    raw_id_fields = ['who']


@admin.register(Location)
class LocationAdmin(VersionAdmin):
    search_fields = ['short_desc']


@admin.register(ParkingPermitPayment)
class ParkingPermitPaymentAdmin(VersionAdmin):
    pass


class ToolInline(admin.TabularInline):

    def more_info(self, obj):
        if obj.id is None:
            return "n/a"
        else:
            # TODO: Use reverse as in the answer at http://stackoverflow.com/questions/2857001
            url_str = "/admin/inventory/tool/{}".format(obj.id)
            return format_html("<a href='{}'>Tool Details</a>", url_str)

    model = Tool
    extra = 0

    fields = ['status', 'short_desc', 'location', 'more_info']
    readonly_fields = ['more_info']


@admin.register(Shop)
class ShopAdmin(VersionAdmin):

    list_display = ['pk', 'name', 'manager', 'backup_manager']
    list_display_links = ['pk', 'name']
    fields = [
        'name',
        ('manager', 'backup_manager'),
        'public_info',
    ]
    raw_id_fields = ['manager', 'backup_manager']
    inlines = [ToolInline]

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


@admin.register(Tool)
class ToolAdmin(VersionAdmin):

    def manager(self, obj):
        return obj.shop.manager

    def backup_mgr(self, obj):
        return obj.shop.backup_manager

    list_display = ['pk', 'short_desc', 'status', 'shop', 'manager', 'backup_mgr', 'loaned_by', 'location']

    list_display_links = ['pk', 'short_desc']

    list_filter = ['status', 'shop', 'is_loaned']

    fields = [
        'short_desc',
        'shop',
        'status',
        'public_info',
        'location',
    ]

    search_fields = ['short_desc']

    raw_id_fields = ['location']

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


def pluralize(s: str, n: int) -> str:
    if n == 1:
        return s
    if " of " in s:
        if "x of " in s:
            return s.replace("x of", "xes of")
        else:
            return s.replace(" of ", "s of ")
    else:
        if s.endswith("x"):
            return s+"es"
        else:
            return s+"s"


@admin.register(ConsumableToStock)
class ConsumableToStockAdmin(VersionAdmin):

    class StatusFilter(admin.SimpleListFilter):
        title = "Status"
        parameter_name = "stat"

        def lookups(self, request, model_admin):
            return (
                ('OK', "Stock Level OK"),
                ('BUY', "Need to Buy"),
            )

        def queryset(self, request, queryset):
            if self.value() == 'OK':
                return queryset.filter(curr_level__gte=F('min_level'))
            if self.value() == 'BUY':
                return queryset.filter(curr_level__lt=F('min_level'))

    def restock_field(self, obj:ConsumableToStock) -> str:
        if obj.curr_level < obj.min_level:
            n = math.ceil(obj.min_level-obj.curr_level)  # type: int
            s = pluralize(obj.level_unit, n)  # type: str
            return "Buy {} {}".format(n, s)
        else:
            return "OK"

    restock_field.short_description = "Status"

    list_display = [
        'pk',
        'short_desc',
        'curr_level',
        'min_level',
        'level_unit',
        'for_shop',
        'stocker',
        'restock_field',
        'obtain_from',
    ]

    list_display_links = ['pk', 'short_desc']

    fields = [
        'short_desc',
        ('obtain_from', 'product_url'),
        ('curr_level', 'min_level', 'level_unit'),
        'for_shop',
        'stocker',
    ]

    list_filter = ['obtain_from', StatusFilter]

    raw_id_fields = ['stocker']

    search_fields = ['short_desc']

    class Media:
        css = {
            "all": ("inventory/styles.css",)
        }

    # curr_level and min_level should have steps of 0.25. They're DecimalFields.
    formfield_overrides = {
        DecimalField: {'widget': NumberInput(attrs={'step': 0.25})},
    }