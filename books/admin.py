
# Standard
from decimal import Decimal

# Third Party
from django.contrib.auth.models import User
from django.db.models import Case, When, Sum, F, Value
from django.db.models.functions import Coalesce
from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django import forms
from django.utils.translation import ugettext_lazy as _
from reversion.admin import VersionAdmin

# Local
from books.models import (
    Account, DonationNote, MonetaryDonation, DonatedItem, Donation,
    Sale, SaleNote, OtherItem, OtherItemType, ExpenseTransaction,
    ExpenseTransactionNote, ExpenseClaim, ExpenseClaimNote,
    ExpenseClaimReference, ExpenseLineItem, AccountGroup, Invoice,
    Entity, EntityNote, InvoiceNote, InvoiceReference
)
from modelmailer.admin import ModelMailerAdmin


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Checksum Admin Form
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def get_ChecksumAdminForm(themodel):
    class ChecksumAdminForm(forms.ModelForm):
        # See http://stackoverflow.com/questions/4891506/django-faking-a-field-in-the-admin-interface

        def __init__(self, *args, **kwargs):
            obj = kwargs.get('instance')
            if obj:  # Only change attributes if an instance is passed
                self.checksum = forms.DecimalField(required=False, initial=obj.checksum())  # Calculated field not saved in database
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

    search_fields = ['name', 'description']

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

    list_filter = ['category', 'type']


class AccountForAccountGroup_Inline(admin.TabularInline):

    def acct_desc(self, obj):
        return obj.account.description
    acct_desc.short_description = "Account description"

    model = AccountGroup.accounts.through
    model._meta.verbose_name = "Account"
    model._meta.verbose_name_plural = "Accounts"
    extra = 0
    fields = ["account", "acct_desc"]
    readonly_fields = ["acct_desc"]
    raw_id_fields = ["account"]


@admin.register(AccountGroup)
class AccountGroupAdmin(VersionAdmin):
    list_display = ['pk', 'name', 'description']
    fields = ['name', 'description']
    inlines = [AccountForAccountGroup_Inline]

    class Media:
        css = {
            "all": (
                "abutils/admin-tabular-inline.css",  # Hides "denormalized obj descs", to use Woj's term.
            )
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# DONATIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class DonationNoteInline(NoteInline):
    model = DonationNote


class MonetaryDonationInline(admin.StackedInline):
    model = MonetaryDonation
    fields = ['amount']
    extra = 0


class DonatedItemInline(admin.TabularInline):
    model = DonatedItem
    extra = 0


@admin.register(Donation)
class DonationAdmin(ModelMailerAdmin, VersionAdmin):

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

    class Media:
        css = {
            "all": (
                "books/admin.css",  # Sizes "description" to a more reasonable height.
                "abutils/admin-tabular-inline.css",  # Hides "denormalized obj descs", to use Woj's term.
            )
        }

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ENTITY
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class EntityNoteInline(NoteInline):
    model = EntityNote

@admin.register(Entity)
class EntityAdmin(VersionAdmin):
    inlines = [EntityNoteInline]


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# INVOICE
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class InvoiceNoteInline(NoteInline):
    model = InvoiceNote


class InvoiceStatusFilter(admin.SimpleListFilter):
    title = "Invoice Status"
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('open', _('Open')),
            ('closed', _('Closed')),
        )

    def annotate_total_paid(self, queryset):
        return queryset.annotate(
            total_paid=Coalesce(
                Sum(
                    Case(
                        When(invoicereference__id__isnull=True, then=Value("0.00")),
                        When(invoicereference__portion__isnull=False, then=F('invoicereference__portion')),
                        When(invoicereference__portion__isnull=True, then=F('amount')),
                    )
                ),
                Value("0.00"),
            )
        )

    def queryset(self, request, queryset):

        if self.value() == 'open':
            # An invoice with total paid < amount invoiceed is "open"
            return self.annotate_total_paid(queryset).filter(total_paid__lt=F('amount'))

        if self.value() == 'closed':
            # Anything that has been fully paid is "closed"
            return self.annotate_total_paid(queryset).filter(total_paid=F('amount'))


@admin.register(Invoice)
class InvoiceAdmin(VersionAdmin):

    list_display = [
        'id',
        'date_invoiced',
        'user_invoiced',
        'entity_invoiced',
        'amount',
        'account',
    ]

    fields = [
        'id',
        'date_invoiced',
        ('user_invoiced', 'entity_invoiced'),
        'amount',
        'description',
        'account',
    ]

    raw_id_fields = ['user_invoiced', 'entity_invoiced', 'account']

    readonly_fields = ['id']

    date_hierarchy = 'date_invoiced'

    inlines = [InvoiceNoteInline]

    list_filter = [InvoiceStatusFilter]

    search_fields = [
        'entity_invoiced__name',
        'entity_invoiced__email',
        '^user_invoiced__first_name',
        '^user_invoiced__last_name',
        '^user_invoiced__username',
        'user_invoiced__email',
    ]


class InvoiceReferenceInline(admin.StackedInline):
    model = InvoiceReference
    extra = 0

    def invoice_link(self, obj):
        # TODO: Use reverse as in the answer at http://stackoverflow.com/questions/2857001
        url_str = "/admin/books/invoice/{}".format(obj.invoice.id)
        return format_html("<a href='{}'>View Invoice</a>", url_str)

    raw_id_fields = ['invoice']
    readonly_fields = ['invoice_link']


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
    readonly_fields = ['ctrlid']


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

    #TODO: Move to Sale model?
    def name_col(self, obj: Sale):
        result = ""
        if obj.payer_acct is not None:
            u = obj.payer_acct  # type: User
            n = " ".join(filter(None, [u.first_name, u.last_name]))
            result = n if len(n) > len(result) else result
        # TODO: Will have entity_account's name here, eventually
        if obj.payer_name > "":
            n = obj.payer_name
            result = n if len(n) > len(result) else result
        return result
    name_col.short_description = "Payer"

    #TODO: Move to Sale model?
    def acct_type_col(self, obj: Sale):
        if obj.payer_acct is not None:
            return "U"
        # TODO: Will have entity_account's name here, eventually
        if obj.payer_name > "":
            return "-"
    acct_type_col.short_description = "T"

    list_display = [
        'pk',
        'sale_date',
        'acct_type_col',
        'name_col',
        'payment_method',
        'method_detail',
        'total_paid_by_customer',
        'processing_fee',
        'deposit_date',
    ]
    fields = [
        ('sale_date', 'deposit_date'),
        'payer_acct',
        ('payer_name', 'payer_email'),
        ('payment_method','method_detail'),
        ('total_paid_by_customer', 'checksum'),
        'processing_fee',
        'protected',
        'ctrlid',
    ]
    raw_id_fields = ['payer_acct']
    list_display_links = ['pk']
    ordering = ['-sale_date']
    inlines = [
        SaleNoteInline,
        MonetaryDonationInline,
        OtherItemInline,
        InvoiceReferenceInline,
    ]
    readonly_fields = ['ctrlid', 'checksum']
    search_fields = [
        'payer_name',
        'payer_email',
        #TODO: 'entity_acct__name',
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


class ClaimStatusFilter(admin.SimpleListFilter):
    title = "Claim Status"
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('open', _('Open')),
            ('submitted', _('Submitted')),
            ('closed', _('Closed')),
        )

    def annotate_total_paid(self, queryset):
        return queryset.annotate(
            total_paid=Coalesce(
                Sum(
                    Case(
                        When(expenseclaimreference__id__isnull=True, then=Value("0.00")),
                        When(expenseclaimreference__portion__isnull=False, then=F('expenseclaimreference__portion')),
                        When(expenseclaimreference__portion__isnull=True, then=F('amount')),
                    )
                ),
                Value("0.00"),
            )
        )

    def queryset(self, request, queryset):

        if self.value() == 'open':
            # An claim with total paid < amount claimed is "open"
            return self.annotate_total_paid(queryset).filter(total_paid__lt=F('amount'))

        if self.value() == 'submitted':
            # "Submitted" is the same as "open" but also has a non-null submission date.
            return self.annotate_total_paid(queryset).filter(total_paid__lt=F('amount'), when_submitted__isnull=False)

        if self.value() == 'closed':
            # Anything that has been fully paid is "closed", whether submission date is null or not.
            return self.annotate_total_paid(queryset).filter(total_paid=F('amount'))


@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(VersionAdmin):

    form = get_ChecksumAdminForm(ExpenseClaim)

    def remaining_fmt(self, obj):
        result = obj.remaining()
        return result if result > 0 else "-"
    remaining_fmt.short_description = "unpaid"

    def paid_fmt(self, obj):
        result = obj.reimbursed()
        return result if result > 0 else "-"
    paid_fmt.short_description = "paid"

    def status_fmt(self, obj):
        return obj.status_str()
    status_fmt.short_description = "Status"

    list_display = [
        'pk',
        'claimant',
        'amount',
        'paid_fmt',
        'remaining_fmt',
        'when_submitted',
        'status_fmt',
        # 'is_reimbursed',
        # 'checksum_fmt',  Too slow to include here.
    ]
    list_filter = [
        ClaimStatusFilter,
        ('claimant',admin.RelatedOnlyFieldListFilter)
    ]
    fields = [
        'id',
        'claimant',
        ('amount', 'checksum'),
        ('when_submitted', 'submit'),
    ]
    ordering = ['-when_submitted']
    readonly_fields = ['id', 'when_submitted', 'checksum']
    inlines = [
        ExpenseClaimNoteInline,
        ExpenseLineItemInline,
        # ReimbursementInline,
    ]
    search_fields = [
        '^claimant__first_name',
        '^claimant__last_name',
        '^claimant__username',
        'claimant__email',
        'expenselineitem__receipt_num',
        'expenselineitem__description',
        'expenselineitem__account__name',
    ]
    raw_id_fields = ['claimant']

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# EXPENSE TRANSACTIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# REVIEW: Following class is very similar to MemberTypeFilter. Can they be combined?
class ExpenseTypeFilter(admin.SimpleListFilter):
    title = "Type"
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return (
            ('claims', _('One or more claims')),
            ('none', _('No claims')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'claims':
            return queryset.filter(expenseclaimreference__isnull=False)
        if self.value() == 'none':
            return queryset.filter(expenseclaimreference__isnull=True)


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

    #TODO: Move to ExpenseTransaction model?
    def name_col(self, obj: ExpenseTransaction):
        result = ""
        if obj.recipient_acct is not None:
            u = obj.recipient_acct  # type: User
            n = " ".join(filter(None, [u.first_name, u.last_name]))
            result = n if len(n) > len(result) else result
        if obj.recipient_entity is not None:
            e = obj.recipient_entity  # type: Entity
            n = e.name
            result = n if len(n) > len(result) else result
        if obj.recipient_name > "":
            n = obj.recipient_name
            result = n if len(n) > len(result) else result
        return result
    name_col.short_description = "Recipient"

    #TODO: Move to ExpenseTransaction model?
    def acct_type_col(self, obj: ExpenseTransaction):
        if obj.recipient_acct is not None:
            return "U"
        if obj.recipient_entity is not None:
            return "E"
        if obj.recipient_name > "":
            return "-"
    acct_type_col.short_description = "T"


    search_fields = [
        '^recipient_acct__first_name',
        '^recipient_acct__last_name',
        '^recipient_acct__username',
        'recipient_acct__email',
        'recipient_entity__name',
        'recipient_name',
        'recipient_email',
        'method_detail', # For check numbers
        #TODO: Add line item descriptions?
        #TODO: Add expense claim line item descriptions?
    ]

    list_display = [
        'pk',
        'payment_date',
        'acct_type_col',
        'name_col',
        'amount_paid',
        'payment_method',
        'method_detail'
    ]
    list_filter = ['payment_method', 'payment_date', ExpenseTypeFilter, ('recipient_acct',admin.RelatedOnlyFieldListFilter)]
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']

    fields = [
        'payment_date',
        'recipient_acct',
        'recipient_entity',
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

    raw_id_fields = ['recipient_acct', 'recipient_entity']


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
