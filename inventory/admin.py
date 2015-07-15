from django.contrib import admin
from .models import PermitScan, PermitRenewal, ParkingPermit, Location

class PermitRenewalInline(admin.TabularInline):
    model = PermitRenewal
    extra = 0

class PermitScanInline(admin.TabularInline):
    model = PermitScan
    extra = 0

class ParkingPermitAdmin(admin.ModelAdmin):
    list_display = ['short_desc', 'owner', 'created', 'ok_to_move', 'is_in_inventoried_space']
    fields = ['short_desc', 'owner', 'created', 'ok_to_move', 'is_in_inventoried_space']
    readonly_fields = ['created']
    inlines = [PermitRenewalInline, PermitScanInline]

admin.site.register(PermitScan)
admin.site.register(Location)
admin.site.register(ParkingPermit, ParkingPermitAdmin)


