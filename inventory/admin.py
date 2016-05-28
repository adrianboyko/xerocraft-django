
# Standard

# Third Party
from django.contrib import admin
from reversion.admin import VersionAdmin

# Local
from inventory.models import PermitScan, PermitRenewal, ParkingPermit, Location


class PermitRenewalInline(admin.TabularInline):
    model = PermitRenewal
    extra = 0


class PermitScanInline(admin.TabularInline):
    model = PermitScan
    extra = 0


@admin.register(ParkingPermit)
class ParkingPermitAdmin(VersionAdmin):
    list_display = ['short_desc', 'owner', 'created', 'ok_to_move', 'is_in_inventoried_space']
    fields = ['short_desc', 'owner', 'created', 'ok_to_move', 'is_in_inventoried_space']
    readonly_fields = ['created']
    inlines = [PermitRenewalInline, PermitScanInline]
    raw_id_fields = ['owner']


@admin.register(PermitScan)
class PermitScanAdmin(VersionAdmin):
    list_display = ['pk', 'when', 'permit', 'where']


@admin.register(Location)
class LocationAdmin(VersionAdmin):
    pass


@admin.register(PermitRenewal)
class PermitRenewalAdmin(VersionAdmin):
    pass
