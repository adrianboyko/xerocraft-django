
# Standard
from datetime import date

# Third Party
from django.contrib.auth.models import User
from django.db.models import Case, When, Sum, F, Value, Q
from django.db.models.functions import Coalesce
from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from reversion.admin import VersionAdmin
from django_object_actions import DjangoObjectActions

# Local
from books.models import (
    Account, Budget, CashTransfer,
    DonationNote, MonetaryDonation, DonatedItem, Donation, MonetaryDonationReward,
    Sale, SaleNote, OtherItem, OtherItemType, ExpenseTransaction,
    ExpenseTransactionNote, ExpenseClaim, ExpenseClaimNote,
    ExpenseClaimReference, ExpenseLineItem,
    ReceivableInvoice, ReceivableInvoiceNote, ReceivableInvoiceReference, ReceivableInvoiceLineItem,
    PayableInvoice, PayableInvoiceNote, PayableInvoiceReference, PayableInvoiceLineItem,
    Entity, EntityNote,
    Campaign, CampaignNote,
    Journaler,
    BankAccount, BankAccountBalance
)
from modelmailer.admin import ModelMailerAdmin
from books.views import journalentry_view


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# UTILITIES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# TODO: Move to models?
def name_colfunc(user: User, ent: Entity):
    result = ""
    if user is not None:
        n = " ".join(filter(None, [user.first_name, user.last_name]))
        result = n if len(n) > len(result) else result
    if ent is not None:
        n = ent.name
        result = n if len(n) > len(result) else result
    return result


def get_url_str(obj):
    app = obj._meta.app_label
    mod = obj._meta.model_name
    url_name = 'admin:{}_{}_change'.format(app, mod)
    url_str = reverse(url_name, args=[obj.id])
    return url_str


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
# JOURNALER ADMIN
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class JournalerAdmin(DjangoObjectActions, VersionAdmin):
    """Adds a 'Journal Entries' button to admin views that display Journalers. """

    def viewjournal_action(self, request, obj: Journaler):
        return journalentry_view(request, obj)

    def save_related(self, request, form, formsets, change):
        """This method is overriden because it's the logical place to journal the transaction after it's changed."""
        super(VersionAdmin, self).save_related(request, form, formsets, change)
        form.instance.journal_one_transaction()

    viewjournal_action.label = "Journal Entries"
    viewjournal_action.short_description = "View the journal entries (accounting) for this transaction."
    # change_actions = ['viewjournal_action']

    view_on_site = False


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# NOTES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class NoteInline(admin.TabularInline):

    fields = ['needs_attn', 'content']

    readonly_fields = []
    raw_id_fields = []

    extra = 0

    class Meta:
        abstract = True


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ACCOUNTS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class AccountParentFilter(admin.SimpleListFilter):
    title = "parent"
    parameter_name = 'parent'

    def lookups(self, request, model_admin):
        accts = Account.objects.all()
        return [(a.id, a.name) for a in accts if len(a.subaccounts)>0]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(Q(active=True)&(Q(parent=self.value())|Q(id=self.value())))


@admin.register(Account)
class AccountAdmin(VersionAdmin):

    class SubAccountInline(admin.TabularInline):

        def sub_link(self, obj) -> str:
            url_str = get_url_str(obj)
            return format_html("<a href='{}'>{}</a>", url_str, obj.name)
        sub_link.allow_tags = True
        sub_link.short_description = "Name"

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

        model = Account
        extra = 0
        fields = ['pk', 'sub_link', 'manager', 'description']
        readonly_fields = ['pk', 'sub_link', 'manager', 'description']
        verbose_name = "Subaccount"
        verbose_name_plural = "Subaccounts"

    inlines = [SubAccountInline]

    list_display = [
        'pk',
        'name',
        'parent',
        'category', 'type',
        #'manager',
        'description',
    ]

    list_display_links = ['pk', 'name']

    fields = [
        ('name', 'parent'),
        ('category', 'type'),
        'manager',
        'description',
        'active',
    ]

    raw_id_fields = ['manager', 'parent']

    list_filter = ['category', 'type', AccountParentFilter]

    search_fields = ['=id', 'description', 'name']

    class Media:
        css = {
            "all": (
                "abutils/admin-tabular-inline.css",  # Hides "denormalized obj descs", to use Woj's term.
            )
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# BUDGET
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(Budget)
class BudgetAdmin(JournalerAdmin):

    class CoveredAcctInline(admin.TabularInline):
        model = Budget.for_accts.through
        model._meta.verbose_name = "Covered Account"
        model._meta.verbose_name_plural = "Covered Accounts"
        raw_id_fields = ['account']
        extra = 0

    list_display = ['pk', 'name', 'year', 'amount', 'from_acct', 'to_acct']
    list_display_links = ['pk', 'name']
    fields = ['name', 'year', 'amount', 'from_acct', 'to_acct']
    raw_id_fields = ['from_acct', 'to_acct']
    change_actions = ['viewjournal_action']  # DjangoObjectActions
    inlines = [CoveredAcctInline]
    list_filter = ['year']

    class Media:
        css = {
            "all": (
                "abutils/admin-tabular-inline.css",  # Hides "denormalized obj descs", to use Woj's term.
            )
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CASH TRANSFERS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(CashTransfer)
class CashTransferAdmin(JournalerAdmin):
    list_display = ['pk', 'when', 'amount', 'from_acct', 'to_acct', 'why']
    list_display_links = ['pk']
    raw_id_fields = ['from_acct', 'to_acct']
    change_actions = ['viewjournal_action']  # DjangoObjectActions


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# DONATIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(MonetaryDonationReward)
class MonetaryDonationRewardAdmin(VersionAdmin):
    list_display = ['pk', 'name', 'min_donation', 'fair_mkt_value', 'cost_to_org']
    list_display_links = ['pk', 'name']


class DonationNoteInline(NoteInline):
    model = DonationNote


class MonetaryDonationInline(admin.StackedInline):
    model = MonetaryDonation
    fields = [
        'amount',
        'earmark',
        'reward',
    ]
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

    change_actions = ['email_action']  # DjangoObjectActions

    class Media:
        css = {
            "all": (
                "books/admin.css",  # Sizes "description" to a more reasonable height.
                "abutils/admin-tabular-inline.css",  # Hides "denormalized obj descs", to use Woj's term.
            )
        }


@admin.register(Campaign)
class CampaignAdmin(VersionAdmin):

    class CampaignNoteInline(admin.TabularInline):  # Can't inherit from NoteInline b/c of extra field.
        model = CampaignNote
        fields = ['author', 'is_public', 'content']
        extra = 0
        raw_id_fields = ['author']

    class MonetaryDonationInlineForCampaign(admin.TabularInline):
        model = MonetaryDonation

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

        def when_field(self, obj):
            return str(obj.sale.sale_date)
        when_field.short_description = "Date"

        def who_field(self, obj):
            return obj.sale.payer_str
        who_field.short_description = "Who"

        fields = [
            'when_field',
            'who_field',
            'amount',
            'reward',
        ]
        readonly_fields = [
            'when_field',
            'who_field',
            'amount',
            'reward',
        ]
        extra = 0

    list_display = ['pk', 'name', 'target_amount', 'cash_account', 'revenue_account']
    list_display_links = ['pk', 'name']
    raw_id_fields = ['cash_account', 'revenue_account']
    inlines = [CampaignNoteInline, MonetaryDonationInlineForCampaign]

    class Media:
        css = {
            "all": (
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
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']
    inlines = [EntityNoteInline]


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# INVOICES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def make_InvoiceStatusFilter(invtype: str):

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
                            When(**{
                                invtype+'invoicereference__id__isnull': True,
                                'then': Value("0.00")
                            }),
                            When(**{
                                invtype+'invoicereference__portion__isnull': False,
                                'then': F(invtype+'invoicereference__portion')
                            }),
                            When(**{
                                invtype+'invoicereference__portion__isnull': True,
                                'then': F('amount')
                            }),
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

    return InvoiceStatusFilter


class ReceivableInvoiceNoteInline(NoteInline):
    model = ReceivableInvoiceNote


class PayableInvoiceNoteInline(NoteInline):
    model = PayableInvoiceNote


class ReceivableInvoiceLineItemAdmin(admin.TabularInline):
    extra = 0
    model = ReceivableInvoiceLineItem
    raw_id_fields = ['account']


class PayableInvoiceLineItemAdmin(admin.TabularInline):
    model = PayableInvoiceLineItem
    raw_id_fields = ['account']


class InvoiceAdmin(JournalerAdmin):

    list_display = [
        'id',
        'invoice_date',
        'name_col',
        'amount',
        'description',
    ]

    fields = [
        'id',
        'invoice_date',
        ('user', 'entity'),
        ('amount', 'checksum'),
        'description',
    ]

    raw_id_fields = ['user', 'entity']

    readonly_fields = ['id', 'checksum']

    date_hierarchy = 'invoice_date'

    search_fields = [
        'entity__name',
        'entity__email',
        '^user__first_name',
        '^user__last_name',
        '^user__username',
        'user__email',
    ]

    change_actions = ['viewjournal_action']  # DjangoObjectActions

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


@admin.register(ReceivableInvoice)
class ReceivableInvoiceAdmin(InvoiceAdmin, ModelMailerAdmin):

    def name_col(self, obj: ReceivableInvoice):
        return name_colfunc(obj.user, obj.entity)
    name_col.short_description = "To"

    form = get_ChecksumAdminForm(ReceivableInvoice)

    inlines = [ReceivableInvoiceNoteInline, ReceivableInvoiceLineItemAdmin]
    list_filter = [make_InvoiceStatusFilter('receivable')]

    fields = InvoiceAdmin.fields + ['send_invoice']
    change_actions = ['viewjournal_action', 'email_action']  # DjangoObjectActions


@admin.register(PayableInvoice)
class PayableInvoiceAdmin(InvoiceAdmin):

    def name_col(self, obj: ReceivableInvoice):
        return name_colfunc(obj.user, obj.entity)
    name_col.short_description = "From"

    form = get_ChecksumAdminForm(PayableInvoice)

    inlines = [PayableInvoiceNoteInline, PayableInvoiceLineItemAdmin]
    list_filter = [make_InvoiceStatusFilter('payable'), 'subject_to_1099']

    list_display = [
        'id',
        'invoice_date',
        'name_col',
        'amount',
        'subject_to_1099',
        'description',
    ]

    fields = [
        'id',
        'invoice_date',
        ('user', 'entity'),
        ('amount', 'checksum'),
        'description',
        'subject_to_1099',
    ]


class ReceivableInvoiceReferenceInline(admin.TabularInline):
    model = ReceivableInvoiceReference
    extra = 0
    raw_id_fields = ['invoice']


class PayableInvoiceReferenceInline(admin.TabularInline):
    model = PayableInvoiceReference
    extra = 0
    raw_id_fields = ['invoice']


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
        'revenue_acct',
    ]


@admin.register(Sale)
class SaleAdmin(JournalerAdmin, ModelMailerAdmin):

    @staticmethod
    def link_to_user(modeladmin, request, queryset) -> None:
        # TODO: This should be an asynchronous task if we're going to allow its use on large sets.
        for obj in queryset.filter(payer_acct__isnull=True):  # type: Sale
            if obj.link_to_user():
                obj.save()

    actions = ['link_to_user']

    form = get_ChecksumAdminForm(Sale)

    # TODO: Move to Sale model?
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

    # TODO: Move to Sale model?
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
        ('processing_fee', 'fee_payer'),
        'send_receipt',
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
        ReceivableInvoiceReferenceInline,
    ]
    readonly_fields = ['ctrlid', 'checksum']
    search_fields = [
        '^id',
        'payer_name',
        'payer_email',
        #TODO: 'entity_acct__name',
        '^payer_acct__first_name',
        '^payer_acct__last_name',
        '^payer_acct__username',
        'payer_acct__email',
        'salenote__content',
        'monetarydonation__earmark__name',
        'otheritem__type__name',
        'otheritem__type__revenue_acct__name',
        'total_paid_by_customer',
        '^ctrlid',
    ]
    list_filter = ['payment_method', 'sale_date']
    date_hierarchy = 'sale_date'

    change_actions = ['viewjournal_action', 'email_action']  # DjangoObjectActions


    class Media:
        css = {
            "all": (
                "books/admin.css",  # Sizes "description" to a more reasonable height.
                "abutils/admin-tabular-inline.css",  # Hides "denormalized obj descs", to use Woj's term.
            )
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# EXPENSE CLAIMS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ExpenseClaimNoteInline(NoteInline):
    model = ExpenseClaimNote


class ExpenseLineItemInline(admin.TabularInline):
    model = ExpenseLineItem
    fields = [
        'bought_from',
        'receipt_num',
        'expense_date',
        'description',
        'account',
        'amount',
        'discount',
        'approved_by',
    ]
    raw_id_fields = ['bought_from', 'approved_by']
    extra = 0

    class Media:
        css = {
        "all": ("books/expense-lineitem-inline.css",)
        }


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
            return self.annotate_total_paid(queryset)\
                .filter(total_paid__lt=F('amount'))\
                .filter(donate_reimbursement=False)

        if self.value() == 'submitted':
            # "Submitted" is the same as "open" but also has a non-null submission date.
            return self.annotate_total_paid(queryset).filter(total_paid__lt=F('amount'), when_submitted__isnull=False)

        if self.value() == 'closed':
            # Anything that has been fully paid is "closed", whether submission date is null or not.
            # Anything marked as "donate reimbursement" is "closed", whether submission date is null or not.
            return self.annotate_total_paid(queryset).filter(
                Q(total_paid=F('amount')) | Q(donate_reimbursement=True)
            )


@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(JournalerAdmin):

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
        ('claimant', admin.RelatedOnlyFieldListFilter)
    ]
    fields = [
        'id',
        'claimant',
        ('amount', 'checksum'),
        ('when_submitted', 'submit'),
        'donate_reimbursement',
    ]
    ordering = ['-when_submitted']
    readonly_fields = ['id', 'when_submitted', 'checksum']
    inlines = [
        ExpenseClaimNoteInline,
        ExpenseLineItemInline,
        # ReimbursementInline,
    ]
    search_fields = [
        '^id',
        '^claimant__first_name',
        '^claimant__last_name',
        '^claimant__username',
        'claimant__email',
        'expenselineitem__receipt_num',
        'expenselineitem__description',
        'expenselineitem__account__name',
    ]
    raw_id_fields = ['claimant']

    change_actions = ['viewjournal_action']  # DjangoObjectActions

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


#@admin.register(ExpenseLineItem)
class ExpenseLineItemAdmin(VersionAdmin):

    search_fields = [
        '^id',
        'amount',
    ]

    list_display =  [
        'pk',
        'expense_date',
        'amount',
        'description',
    ]

    list_display_links = [
        'pk',
        'description',
    ]

    fields = [
        ('exp', 'claim'),
        'description',
        'amount',
        'expense_date',
        'receipt_num',
        'account',
        'approved_by',
    ]

    raw_id_fields = ['approved_by']
    readonly_fields = ['exp', 'claim']


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
    raw_id_fields = ['claim']


@admin.register(ExpenseTransaction)
class ExpenseTransactionAdmin(JournalerAdmin):

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
        '^id',
        '^recipient_acct__first_name',
        '^recipient_acct__last_name',
        '^recipient_acct__username',
        'recipient_acct__email',
        'recipient_entity__name',
        'recipient_name',
        'recipient_email',
        'method_detail', # For check numbers
        'expensetransactionnote__content',
        'expenselineitem__description',
        'amount_paid'

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
        PayableInvoiceReferenceInline,
    ]

    raw_id_fields = ['recipient_acct', 'recipient_entity']

    change_actions = ['viewjournal_action']  # DjangoObjectActions

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# BANK ACCOUNTS AND BALANCES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


@admin.register(BankAccount)
class BankAccountAdmin(VersionAdmin):
    list_display = ['pk', 'name', 'description']


# REVIEW: Following class is very similar to MemberTypeFilter. Can they be combined?
class BalanceOrderFilter(admin.SimpleListFilter):
    title = "order on date"
    parameter_name = 'ood'

    def lookups(self, request, model_admin):
        return (
            ('eod', _('Only end of day')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'eod':
            return queryset.filter(order_on_date=0)

@admin.register(BankAccountBalance)
class BankAccountBalanceAdmin(VersionAdmin):
    list_display = ['pk', 'bank_account', 'when', 'order_on_date', 'balance']
    list_filter = ['bank_account__name', BalanceOrderFilter]
    date_hierarchy = 'when'


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# DECORATORS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# These allow StackedInlines in other apps to be hooked into this Books app.
# This approach keeps the dependencies one-way *towards* Books.

class Inlineable:
    model_cls = None
    container_cls = None

    def __init__(self, model_cls, container_cls):
        if not issubclass(model_cls, models.Model):
            raise ValueError('Wrapped class must subclass django.db.models.Model.')
        self.model_cls = model_cls
        self.container_cls = container_cls

    def __call__(self, inline_cls):
        inline_cls.model = self.model_cls
        isStacked = issubclass(inline_cls, admin.StackedInline)
        isTabular = issubclass(inline_cls, admin.TabularInline)
        if not isStacked and not isTabular:
            raise ValueError('Wrapped class must subclass InlineModelAdmin.')
        admin.site._registry[self.container_cls].inlines.append(inline_cls)
        return inline_cls


class Sellable(Inlineable):
    def __init__(self, model_cls):
        super().__init__(model_cls, Sale)


class Invoiceable(Inlineable):
    def __init__(self, model_cls):
        super().__init__(model_cls, ReceivableInvoice)
