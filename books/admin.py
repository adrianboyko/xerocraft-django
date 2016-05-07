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


class DonatedItemInline(admin.StackedInline):
    model = DonatedItem
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
        'send_receipt',
    ]
    raw_id_fields = ['donator_acct']
    ordering = ['-donation_date']
    inlines = [DonationNoteInline, DonatedItemInline]
    search_fields = [
        'donator_name',
        'donator_email',
        '^donator_acct__first_name',
        '^donator_acct__last_name',
        '^donator_acct__username',
        'donator_acct__email',
    ]


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# SALES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def sale_link(self, obj):
    return "<a href='/admin/books/sale/{}/'>{}</a>".format(obj.sale.id, obj.sale)
sale_link.allow_tags = True


# @admin.register(OtherItem)  # I don't normally want this to appear since there's already an inline.
class OtherItemAdmin(VersionAdmin):

    sale_link = sale_link

    list_display = [
        'pk',
        'ctrlid',  # Temporary
        'type',
        'qty_sold',
        'sale_price',
        'sale_link',
    ]

    raw_id_fields = ['sale']
    readonly_fields = ['ctrlid']


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
    search_fields = [
        'payer_name',
        'payer_email',
        '^payer_acct__first_name',
        '^payer_acct__last_name',
        '^payer_acct__username',
        'payer_acct__email',
    ]
    list_filter = ['payment_method', 'sale_date']
    date_hierarchy = 'sale_date'


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# EXPENSE CLAIMS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ExpenseClaimNoteInline(NoteInline):
    model = ExpenseClaimNote


class ExpenseLineItemInline(admin.TabularInline):
    model = ExpenseLineItem
    fields = [
        'receipt_num',
        'expense_date',
        'description',
        'account',
        'amount',
    ]
    extra = 0


@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(VersionAdmin):
    list_display = [
        'pk',
        'claim_date',
        'amount',
        'claimant',
    ]
    ordering = ['-claim_date']
    inlines = [
        ExpenseClaimNoteInline,
        ExpenseLineItemInline,
    ]
    search_fields = [
        '^claimant__first_name',
        '^claimant__last_name',
        '^claimant__username',
        'claimant__email',
    ]
    raw_id_fields = ['claimant']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# EXPENSE TRANSACTIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ExpenseClaimReferenceInline(admin.StackedInline):
    model = ExpenseClaimReference
    extra = 0
    raw_id_fields = ['claim']


@admin.register(ExpenseTransaction)
class ExpenseTransactionAdmin(VersionAdmin):
    list_display = [
        'pk',
        'payment_date',
        'recipient_acct',
        'recipient_name',
        'recipient_email',
        'amount_paid',
        'payment_method',
        'method_detail'
    ]

    fields = [
        'payment_date',
        'recipient_acct',
        ('recipient_name', 'recipient_email'),
        ('payment_method', 'method_detail'),
        'amount_paid',
    ]

    inlines = [ExpenseLineItemInline, ExpenseClaimReferenceInline]

    raw_id_fields = ['recipient_acct']


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
