from django.contrib import admin
from django.db import models
from books.models import *
from reversion.admin import VersionAdmin


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# NOTES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class NoteInline(admin.StackedInline):

    fields = ['author', 'content']

    readonly_fields = ['author']

    extra = 0

    class Meta:
        abstract = True


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ACCOUNTS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(Account)
class AccountAdmin(VersionAdmin):
    list_display = [
        'pk',
        'name',
        'category', 'type',
        'manager',
        'description',
    ]
    fields = [
        'name',
        ('category', 'type'),
        'manager',
        'description',
    ]
    raw_id_fields = ['manager']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# DONATIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class DonationNoteInline(NoteInline):
    model = DonationNote


class MonetaryDonationInline(admin.StackedInline):
    model = MonetaryDonation
    fields = ['amount']
    extra = 0


class PhysicalDonationInline(admin.StackedInline):
    model = PhysicalDonation
    extra = 0


@admin.register(Donation)
class DonationAdmin(VersionAdmin):
    list_display = [
        'pk',
        'donation_date',
        'donator_acct',
        'donator_name',
        'donator_email',
    ]
    fields = [
        'donation_date',
        'donator_acct',
        ('donator_name', 'donator_email'),
    ]
    raw_id_fields = ['donator_acct']
    ordering = ['-donation_date']
    inlines = [DonationNoteInline, MonetaryDonationInline, PhysicalDonationInline]
    search_fields = [
        'donator_name',
        'donator_email',
    ]


@admin.register(MonetaryDonation)
class MonetaryDonationAdmin(VersionAdmin):
    pass


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# SALES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SaleNoteInline(NoteInline):
    model = SaleNote


class OtherItemInline(admin.StackedInline):
    model = OtherItem
    extra = 0


@admin.register(OtherItemType)
class OtherItemTypeAdmin(VersionAdmin):
    list_display = [
        'pk',
        'name',
        'description',
    ]


@admin.register(Sale)
class SaleAdmin(VersionAdmin):
    list_display = [
        'pk',
        'sale_date',
        'payer_acct',
        'payer_name',
        'payer_email',
        'payment_method',
        'method_detail',
        'total_paid_by_customer',
        'processing_fee',
    ]
    fields = [
        'sale_date',
        'payer_acct',
        ('payer_name', 'payer_email'),
        ('payment_method','method_detail'),
        'total_paid_by_customer',
        'processing_fee',
        'protected',
        'ctrlid',
    ]
    raw_id_fields = ['payer_acct']
    list_display_links = ['pk']
    ordering = ['-sale_date']
    inlines = [SaleNoteInline, MonetaryDonationInline, OtherItemInline]
    readonly_fields = ['ctrlid']
    search_fields = ['payer_name','payer_email',]
    list_filter = ['payment_method', 'sale_date']
    date_hierarchy = 'sale_date'


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# EXPENSE CLAIMS & REIMBURSEMENT
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ExpenseClaimNoteInline(NoteInline):
    model = ExpenseClaimNote


class MonetaryReimbursementInline(admin.StackedInline):
    model = MonetaryReimbursement
    extra = 0


class ExpenseClaimLineItemInline(admin.StackedInline):
    model = ExpenseClaimLineItem
    extra = 0


@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(VersionAdmin):
    list_display = [
        'pk',
        'claim_date',
        'claimant',
    ]
    ordering = ['-claim_date']
    inlines = [
        ExpenseClaimNoteInline,
        ExpenseClaimLineItemInline,
        MonetaryReimbursementInline,
    ]
    search_fields = [
        '^claimant__first_name',
        '^claimant__last_name',
        '^claimant__username',
    ]
    raw_id_fields = ['claimant']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# DECORATORS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# These allow StackedInlines in other apps to be hooked into this Books app.
# This approach keeps the dependencies one-way *towards* Books.

class Sellable:

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
