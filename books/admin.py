
# Standard

# Third Party
from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from reversion.admin import VersionAdmin
from django import forms

# Local
from books.models import \
    Account, DonationNote, MonetaryDonation, DonatedItem, Donation, \
    Sale, SaleNote, OtherItem, OtherItemType, ExpenseTransaction, \
    ExpenseTransactionNote, ExpenseClaim, ExpenseClaimNote, \
    ExpenseClaimReference, ExpenseLineItem


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Checksum Admin Form
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def get_ChecksumAdminForm(themodel):
    class ChecksumAdminForm(forms.ModelForm):
        # See http://stackoverflow.com/questions/4891506/django-faking-a-field-in-the-admin-interface

        checksum = forms.DecimalField(required=False)  # Calculated field not saved in database

        def __init__(self, *args, **kwargs):
            obj = kwargs.get('instance')
            if obj:  # Only change attributes if an instance is passed
                self.base_fields['checksum'].initial = obj.checksum()
            forms.ModelForm.__init__(self, *args, **kwargs)

        class Meta:
            model = themodel
            fields = "__all__"

    return ChecksumAdminForm

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

    form = get_ChecksumAdminForm(Sale)

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
        ('payer_acct', 'payer_name', 'payer_email'),
        ('payment_method','method_detail'),
        ('total_paid_by_customer', 'checksum'),
        'processing_fee',
        'protected',
        'ctrlid',
    ]
    raw_id_fields = ['payer_acct']
    list_display_links = ['pk']
    ordering = ['-sale_date']
    inlines = [SaleNoteInline, MonetaryDonationInline, OtherItemInline]
    readonly_fields = ['ctrlid', 'checksum']
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
        'approved_by',
    ]
    raw_id_fields = ['approved_by']
    extra = 0


@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(VersionAdmin):

    # TODO: Filter by checksum, dates, account.

    form = get_ChecksumAdminForm(ExpenseClaim)

    list_display = [
        'pk',
        'claimant',
        'amount',
        'when_submitted',
        # 'is_reimbursed',
        # 'checksum_fmt',  Too slow to include here.
    ]
    fields = [
        'claimant',
        ('amount', 'checksum'),
        ('when_submitted', 'submit'),
    ]
    readonly_fields = ['when_submitted', 'checksum']
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

class ExpenseTransactionNoteInline(NoteInline):
    model = ExpenseTransactionNote


class ExpenseClaimReferenceInline(admin.TabularInline):

    model = ExpenseClaimReference
    extra = 0

    def claim_link(self, obj):
        # TODO: Use reverse as in the answer at http://stackoverflow.com/questions/2857001
        url_str = "/admin/books/expenseclaim/{}".format(obj.claim.id)
        return format_html("<a href='{}'>View Claim</a>", url_str)

    raw_id_fields = ['claim']
    readonly_fields = ['claim_link']


@admin.register(ExpenseTransaction)
class ExpenseTransactionAdmin(VersionAdmin):

    form = get_ChecksumAdminForm(ExpenseTransaction)

    search_fields = [
        '^recipient_acct__first_name',
        '^recipient_acct__last_name',
        '^recipient_acct__username',
        'recipient_acct__email',
        '^recipient_name',
        'recipient_email',
        'method_detail',
    ]

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
    list_filter = ['payment_method', 'payment_date']
    date_hierarchy = 'payment_date'

    fields = [
        'payment_date',
        'recipient_acct',
        ('recipient_name', 'recipient_email'),
        ('payment_method', 'method_detail'),
        ('amount_paid', 'checksum'),
    ]

    readonly_fields = ['checksum']

    inlines = [
        ExpenseTransactionNoteInline,
        ExpenseLineItemInline,
        ExpenseClaimReferenceInline,
    ]

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
