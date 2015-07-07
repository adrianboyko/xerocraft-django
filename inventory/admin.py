from django.contrib import admin
from .models import PermitScan, ParkingPermit, Location

class PermitScanInline(admin.TabularInline):
    model = PermitScan
    extra = 0

class ParkingPermitAdmin(admin.ModelAdmin):
    list_display = ['short_desc', 'owner', 'created', 'renewed', 'ok_to_move',]
    fields = ['short_desc', 'owner', 'created', 'renewed', 'ok_to_move',]
    readonly_fields = ['created']
    inlines = [PermitScanInline]

admin.site.register(PermitScan)
admin.site.register(Location)
admin.site.register(ParkingPermit, ParkingPermitAdmin)


