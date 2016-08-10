
# Standard

# Third Party
from django.contrib import admin
from django.utils.html import format_html
from reversion.admin import VersionAdmin

# Local
from inventory.models import PermitScan, PermitRenewal, ParkingPermit, Location, \
    Shop, Tool, ToolIssue, ToolIssueNote


class PermitRenewalInline(admin.TabularInline):
    model = PermitRenewal
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
    list_display = ['pk', 'short_desc', 'owner', 'created', 'ok_to_move', 'is_in_inventoried_space']
    fields = ['short_desc', 'owner', 'created', 'ok_to_move', 'is_in_inventoried_space']
    readonly_fields = ['created']
    inlines = [PermitRenewalInline, PermitScanInline]
    raw_id_fields = ['owner']

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
    pass


@admin.register(PermitRenewal)
class PermitRenewalAdmin(VersionAdmin):
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

    fields = ['status', 'name', 'location', 'more_info']
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


class ToolIssueInline(admin.TabularInline):
    model = ToolIssue
    extra = 0

    def more_info(self, obj):
        if obj.id is None:
            return "n/a"
        else:
            # TODO: Use reverse as in the answer at http://stackoverflow.com/questions/2857001
            url_str = "/admin/inventory/toolissue/{}".format(obj.id)
            return format_html("<a href='{}'>Issue Details</a>", url_str)

    readonly_fields = ['more_info']
    raw_id_fields = ['reporter']


@admin.register(Tool)
class ToolAdmin(VersionAdmin):

    def manager(self, obj):
        return obj.shop.manager

    def backup_mgr(self, obj):
        return obj.shop.backup_manager

    list_display = ['pk', 'name', 'status', 'shop', 'manager', 'backup_mgr', 'location']

    list_display_links = ['pk', 'name']

    list_filter = ['status', 'shop']

    fields = [
        ('name', 'shop', 'status'),
        ('public_info', 'location'),
    ]

    search_fields = ['name']

    inlines = [ToolIssueInline]

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


class ToolIssueNoteInline(admin.StackedInline):
    model = ToolIssueNote
    extra = 0
    raw_id_fields = ['author']
    fields = [
        ('author', 'when_written'),
        'content'
    ]
    readonly_fields = ['when_written']


@admin.register(ToolIssue)
class ToolIssueAdmin(VersionAdmin):

    def shop(self, obj): # Req'd because can't use 'tool__shop' in list_display.
        return obj.tool.shop

    list_display = ['pk', 'tool', 'shop', 'reporter', 'short_desc', 'status', ]
    list_filter = ['status', 'tool__shop']

    fields = [
        'tool',
        ('reporter', 'short_desc'),
        'status',
    ]
    inlines = [ToolIssueNoteInline]
    raw_id_fields = ['reporter']
