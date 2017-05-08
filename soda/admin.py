
# Standard

# Third-party
from django.contrib import admin
from reversion.admin import VersionAdmin


# Local
from .models import Product, SkuToProductMapping, VendingMachineBin, VendLog


@admin.register(Product)
class ProductAdmin(VersionAdmin):
    pass


@admin.register(SkuToProductMapping)
class SkuToProductMappingAdmin(VersionAdmin):
    pass


@admin.register(VendingMachineBin)
class VendingMachineBinAdmin(VersionAdmin):
    pass


@admin.register(VendLog)
class VendLogAdmin(VersionAdmin):
    list_filter = ['product']
    list_display = ['pk', 'when', 'who_for', 'product']
    raw_id_fields = ['who_for']