from django.contrib import admin
from django.db import models
from books.models import *


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# SALES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Sellable:  # A decorator for classes in other apps.

    model_cls = None

    def __init__(self, model_cls):
        if not issubclass(model_cls, models.Model):
            raise ValueError('Wrapped class must subclass django.db.models.Model.')
        self.model_cls = model_cls

    def __call__(self, inline_cls):
        inline_cls.model = self.model_cls
        if not issubclass(inline_cls, admin.StackedInline):
            raise ValueError('Wrapped class must subclass django.contrib.admin.StackedInline.')
        admin.site._registry[Sale].inlines.append(inline_cls)
        return inline_cls


class SaleNoteInline(admin.StackedInline):
    model = SaleNote
    extra = 0
    fields = ['content']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'pk',
        'sale_date',
        'payer_name',
        'payer_email',
        'payment_method',
        'method_detail',
        'total_paid_by_customer',
        'processing_fee',
    ]
    fields = [
        'sale_date',
        ('payer_name', 'payer_email'),
        ('payment_method','payment_detail'),
        'total_paid_by_customer',
        'processing_fee',
    ]
    list_display_links = ['pk']
    ordering = ['-sale_date']
    inlines = [SaleNoteInline]
    readonly_fields = ['ctrlid']
    search_fields = ['payer_name','payer_email',]
    list_filter = ['payment_method', 'sale_date']
    date_hierarchy = 'sale_date'


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# DONATIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class DonationNoteInline(admin.StackedInline):
    model = DonationNote
    extra = 0


class MonetaryDonationInline(admin.StackedInline):
    model = MonetaryDonation
    extra = 0


class PhysicalDonationInline(admin.StackedInline):
    model = PhysicalDonation
    extra = 0


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = [
        'pk',
        'donation_date',
        'donator_name',
        'donator_email',
    ]
    ordering = ['-donation_date']
    inlines = [DonationNoteInline, MonetaryDonationInline, PhysicalDonationInline]
    search_fields = [
        'donator_name',
        'donator_email',
    ]


