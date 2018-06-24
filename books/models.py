# pylint: disable=C0330

# Standard
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from abc import abstractmethod, ABCMeta
from logging import getLogger
from collections import Counter

# Third party
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from nameparser import HumanName
from django.urls import reverse


# Local
from abutils.utils import generate_ctrlid

logger = getLogger("books")

ORG_NAME = settings.BZWOPS_CONFIG['ORG_NAME']

DEC0 = Decimal("0.00")
DEC1 = Decimal("1.00")

ACCT_LIABILITY_PAYABLE = 39
ACCT_LIABILITY_UNEARNED_MSHIP_REVENUE = 46
ACCT_ASSET_RECEIVABLE = 40
ACCT_ASSET_CASH = 1
ACCT_EXPENSE_BUSINESS = 30
ACCT_REVENUE_DONATION = 35  # General Donations.
ACCT_REVENUE_MEMBERSHIP = 6
ACCT_REVENUE_DISCOUNT = 49

try:
    PROD_HOST = Site.objects.get_current().domain
    DEV_HOST = "localhost:8000"
except:
    PROD_HOST = "example.com"
    DEV_HOST = "localhost:8000"


def quote_entity(name: str) -> str:
    return "[{}]".format(name)


# class PayerAKA(models.Model):
#     """ Intended primarily to record name variations that are used in payments, etc. """
#
#     member = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE,
#         help_text="The member who has payments under another name.")
#
#     aka = models.CharField(max_length=50, null=False, blank=False,
#         help_text="The AKA, probably their spouse's name or a simple variation on their own name.")
#
#     class Meta:
#         verbose_name = "Payer AKA"


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CTRLID UTILITIES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


def next_monetarydonation_ctrlid() -> str:
    """Provides an arbitrary default value for the ctrlid field, necessary when data is being entered manually."""
    return generate_ctrlid(MonetaryDonation)


def next_sale_ctrlid() -> str:
    '''Provides an arbitrary default value for the ctrlid field, necessary when check, cash, or gift-card data is being entered manually.'''
    return generate_ctrlid(Sale)


def next_otheritem_ctrlid() -> str:
    """Provides an arbitrary default value for the ctrlid field, necessary when data is being entered manually."""
    return generate_ctrlid(OtherItem)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Note
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Note(models.Model):

    __metaclass__ = ABCMeta

    author = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the note even if the user is deleted.
        help_text="The user who wrote this note.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the item on which this note appears.")

    needs_attn = models.BooleanField(default=False,
        help_text="Check this to indicate that further action is required from some human.")

    def subject_url(self) -> str:
        content_type = ContentType.objects.get_for_model(self.subject.__class__)
        url_name = "admin:{}_{}_change".format(content_type.app_label, content_type.model)
        return reverse(url_name, args=[str(self.subject.id)])

    @property
    @abstractmethod
    def subject(self):
        pass

    def __str__(self):
        return self.content[:40]

    class Meta:
        abstract = True


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Account
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Account(models.Model):

    name = models.CharField(max_length=40, blank=True,
        help_text="Name of the account.")

    parent = models.ForeignKey('self', null=True, blank=True,
        default=None,
        on_delete=models.PROTECT,
        help_text="The parent account for this account, if any.")

    CAT_ASSET     = "A"
    CAT_LIABILITY = "L"
    CAT_EQUITY    = "Q"
    CAT_REVENUE   = "R"
    CAT_EXPENSE   = "X"
    CAT_CHOICES = [
        (CAT_ASSET,     "Asset"),
        (CAT_LIABILITY, "Liability"),
        (CAT_EQUITY,    "Equity"),
        (CAT_REVENUE,   "Revenue"),
        (CAT_EXPENSE,   "Expense"),
    ]
    category = models.CharField(max_length=1, choices=CAT_CHOICES,
        null=False, blank=False,
        help_text="The category of the account.")

    category_names = dict(CAT_CHOICES)

    TYPE_CREDIT = "C"
    TYPE_DEBIT  = "D"
    TYPE_CHOICES = [
        (TYPE_CREDIT, "Credit"),
        (TYPE_DEBIT,  "Debit"),
    ]
    type = models.CharField(max_length=1, choices=TYPE_CHOICES,
        null=False, blank=False,
        help_text="The type of the account.")

    manager = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep this account even if the user is deleted.
        help_text="The user who manages this account.")

    description = models.TextField(max_length=1024,
        help_text="A discussion of the account's purpose. What is it for? What is it NOT for?")

    active = models.BooleanField(default=True,
        help_text="Uncheck when an account is no longer actively used.")

    acct_cache = dict()  # type: Dict[str, Account]

    @staticmethod
    def get(acct_num: int) -> 'Account':
        if acct_num in Account.acct_cache:
            return Account.acct_cache[acct_num]
        try:
            acct = Account.objects.get(id=acct_num)
            Account.acct_cache[acct_num] = acct
            return acct
        except Account.DoesNotExist as e:
            logger.exception("Couldn't find account #{} ".format(acct_num))
            raise

    @property
    def subaccounts(self) -> List['Account']:
        result = []  # type: List['Account']
        for subacct in self.account_set.all():
            result.append(subacct)
            result.extend(subacct.subaccounts)
        return result

    def is_subaccount_of(self, other: 'Account') -> bool:
        if self.parent is None:
            return False
        if self.parent == other:
            return True
        return self.parent.is_subaccount_of(other)

    @property
    def category_name(self):
        return Account.category_names[self.category]

    def __str__(self):
        return self.name

    def clean(self):
        self.dbcheck()

    def dbcheck(self):
        if self.parent is not None:
            if self.parent.category != self.category:
                raise ValidationError("Subaccount must have the same category as it's parent.")
            if self.parent.type != self.type:
                raise ValidationError("Subaccount must have the same type as it's parent.")

    class Meta:
        ordering = ['name']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# JOURNAL - The journal is generated (and regenerated) from other models
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class JournalEntry(models.Model):

    frozen = models.BooleanField(default=False,
        help_text="If frozen, this entry (and its lines) won't be deleted/regenerated.")

    source_url = models.URLField(blank=False, null=False,
        help_text="URL to retrieve the item that gave rise to this journal entry.")

    when = models.DateField(null=False, blank=False,
        help_text="The date of the transaction.")

    unbalanced = models.BooleanField(default=False,
        help_text="Indicates that the entry is unbalanced. Human intervention required, if true.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prebatched lineitems are JournalEntryLineItems that are waiting for their associated
        # JournalEntry to get a PK in the database, at which time they'll have their
        # journal_entry_id assigned and they'll be batched.
        self.prebatched_lineitems = []  # type:List[JournalEntryLineItem]

    def prebatch(self, jeli: 'JournalEntryLineItem'):
        self.prebatched_lineitems.append(jeli)
        return jeli

    def process_prebatch(self):
        self._simplify_prebatched_lineitems()
        if len(self.prebatched_lineitems) == 0:
            url = self.source_url
            if settings.ISDEVHOST:
                url = url.replace(PROD_HOST, DEV_HOST)
            print("Journal Entry for {} has no line items!".format(url))
        for jeli in self.prebatched_lineitems:
            jeli.journal_entry_id = self.id
            JournalLiner.batch_jeli(jeli)
        self.prebatched_lineitems = []

    def _simplify_prebatched_lineitems(self) -> None:
        """Merge line items that are identical except for amount."""

        # Process the current prebatched line items using a Counter to merge them.
        # We need to convert amounts to pennies because Counter only works with ints.
        merger = Counter()
        pennies_per_dollar = Decimal("100.00")
        for jeli in self.prebatched_lineitems:
            key = (jeli.account, jeli.description)
            sign = 1 if jeli.action == jeli.ACTION_BALANCE_INCREASE else -1
            pennies = int(jeli.amount * pennies_per_dollar)
            merger.update({key: sign*pennies})

        # Regenerate the prebatched line items from the Counter:
        self.prebatched_lineitems = []
        for ((acct, desc), pennies) in merger.items():
            act = JournalEntryLineItem.ACTION_BALANCE_INCREASE if pennies > 0 else JournalEntryLineItem.ACTION_BALANCE_DECREASE
            if pennies != 0:
                newjeli = JournalEntryLineItem(
                    account=acct,
                    description=desc,
                    amount=Decimal.from_float(abs(pennies/100.0)),
                    action=act
                )
                self.prebatched_lineitems.append(newjeli)


    def debit_and_credit_totals(self) -> Tuple[Decimal, Decimal]:
        total_debits = Decimal(0.0)
        total_credits = Decimal(0.0)
        for line in self.journalentrylineitem_set.all():  # type: JournalEntryLineItem
            if line.iscredit():
                total_credits += line.amount
            else:
                total_debits += line.amount
        return total_debits, total_credits

    def debits_and_credits(self) -> Tuple[List['JournalEntryLineItem'], List['JournalEntryLineItem']]:
        debit_lis = []  # type: List[JournalEntryLineItem]
        credit_lis = []  # type: List[JournalEntryLineItem]
        for line in self.journalentrylineitem_set.all():  # type: JournalEntryLineItem
            if line.iscredit():
                credit_lis.append(line)
            else:
                debit_lis.append(line)
        return debit_lis, credit_lis

    def debits(self) -> List['JournalEntryLineItem']:
        lis = []  # type: List[JournalEntryLineItem]
        for line in self.journalentrylineitem_set.all():  # type: JournalEntryLineItem
            if line.isdebit():
                lis.append(line)
        return lis

    def credits(self) -> List['JournalEntryLineItem']:
        lis = []  # type: List[JournalEntryLineItem]
        for line in self.journalentrylineitem_set.all():  # type: JournalEntryLineItem
            if line.iscredit():
                lis.append(line)
        return lis

    def dbcheck(self):
        # Relationships can't be checked in clean but can be checked later in a "db check" operation.
        total_debits, total_credits = self.debit_and_credit_totals()
        if total_credits != total_debits:
            raise ValidationError(
                _("Total credits do not equal total debits (dr {} != cr {}.").format(total_debits, total_credits)
            )

    def __str__(self):
        return "Journal Entry #{} dated {}".format(self.pk, self.when)

    class Meta:
        ordering = ['when']


class JournalEntryLineItem(models.Model):

    journal_entry = models.ForeignKey(JournalEntry, null=False, blank=False,
        on_delete=models.CASCADE,  # Deletion and regeneration of journal entries will be common.
        help_text="The journal entry that this line item is part of.")

    account = models.ForeignKey(Account, null=False, blank=False,
        on_delete=models.PROTECT,  # Don't allow account to be deleted if transaction lines reference it.
        help_text="The account involved in this line item.")

    # "Increase" can mean 'credit' OR 'debit', depending on the account referenced! The same is true for "Decrease".
    # This approach is intended to make code more intuitive. Note that iscredit() and isdebit() can be used
    # to determine the traditional dual entry bookkeeping status of the line.
    ACTION_BALANCE_INCREASE = ">"
    ACTION_BALANCE_DECREASE = "<"
    ACTION_CHOICES = [
        (ACTION_BALANCE_INCREASE, "Increase"),
        (ACTION_BALANCE_DECREASE, "Decrease"),
    ]
    action = models.CharField(max_length=1, choices=ACTION_CHOICES,
        null=False, blank=False,
        help_text="Is the account balance increased or decreased?")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The amount of the increase or decrease (always positive)",
        validators=[MinValueValidator(DEC0)])

    description = models.CharField(max_length=128, blank=True,
        help_text="A brief description of this line item.")

    def iscredit(self):
        if self.account.type == Account.TYPE_CREDIT:
            return self.action == self.ACTION_BALANCE_INCREASE
        if self.account.type == Account.TYPE_DEBIT:
            return self.action == self.ACTION_BALANCE_DECREASE

    def isdebit(self):
        return not self.iscredit()

    def __str__(self):
        actionstrs = dict(self.ACTION_CHOICES)
        dr_or_cr = "cr" if self.iscredit() else "dr"
        return "Line Item #{}, {} '{}', ${} {}".format(
            self.pk,
            actionstrs[self.action],
            str(self.account),
            self.amount,
            dr_or_cr,
        )


class Journaler(models.Model):

    __metaclass__ = ABCMeta

    _je_batch = list()  # type: List[JournalEntry]
    _link_names_of_relevant_children = None
    _unbalanced_journal_entries = list()  # type: List[JournalEntry]
    _grand_total_debits = Decimal(0.00)
    _grand_total_credits = Decimal(0.00)

    frozen_in_journal = models.BooleanField(default=False,
        help_text="If true, the journal entries for this transaction are frozen and will not be modified.")

    class Meta:
        abstract = True

    def create_journalentry(self):  # TODO: Name should be plural
        """ This public method guards frozen transactions. """
        if self.frozen_in_journal:
            return
        else:
            self._create_journalentries()

    # Each journaler will have its own logic for creating a journal entry.
    @abstractmethod
    def _create_journalentries(self):
        """
        Create JournalEntry instances associated with this Journaler.
        Do not use SomeModel.objects.create(...)!
        Instead, create SomeModel(...) instances and stage them for batch_create using Journaler.batch(...).
        """
        raise NotImplementedError

    @classmethod
    def link_names_of_relevant_children(cls):
        if cls._link_names_of_relevant_children is None:
            related_objects = [
                f for f in cls._meta.get_fields()
                  if (f.one_to_many or f.one_to_one)
                  and f.auto_created
                  and not f.concrete
            ]
            cls._link_names_of_relevant_children = [
                rel.get_accessor_name() for rel in related_objects
                  if (not hasattr(rel.field, 'is_not_parent'))  # Indicates that link is to a PEER transaction and not to a parent transaction.
                  and issubclass(rel.field.model, JournalLiner)
                ]
        return cls._link_names_of_relevant_children

    def create_lineitems_for(self, je: JournalEntry):
        """Discovers the JournalLiner children of this Journaler and asks them to create_journalentry_lineitems."""
        link_names = self.link_names_of_relevant_children()
        for link_name in link_names:
            children = getattr(self, link_name).all()
            for child in children:
                child.create_journalentry_lineitems(je)

    def get_absolute_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        url_name = "admin:{}_{}_change".format(content_type.app_label, content_type.model)
        relative_url = reverse(url_name, args=[str(self.id)])
        return "https://{}{}".format(PROD_HOST, relative_url)

    @classmethod
    def save_je_batch(cls):
        """
        Save the currently batched JournalEntry instances using bulk_create,
        and stage the associated pre-batched JournalEntryLineItems for batch creation.
        """
        # NOTE: As of 1/18/2016, this will only work in Django version 1.10 with Postgres
        JournalEntry.objects.bulk_create(cls._je_batch)
        for je in cls._je_batch:
            je.process_prebatch()
        cls._je_batch = []

    @classmethod
    def batch(cls, je: JournalEntry):
        """Adds a JournalEntry instance to the batch that's accumulating for eventual bulk_create."""
        balance = DEC0
        for jeli in je.prebatched_lineitems:
            if jeli.iscredit():
                balance += jeli.amount
                cls._grand_total_credits += jeli.amount
            else:
                balance -= jeli.amount
                cls._grand_total_debits += jeli.amount
        if abs(balance) > Decimal("0.05"):  # Don't report *small* errors due to rounding.
            cls._unbalanced_journal_entries.append(je)
            je.unbalanced = True
        cls._je_batch.append(je)
        if len(cls._je_batch) > 1000:
            cls.save_je_batch()
        return je

    def journal_one_transaction(self):
        """
        Create and save journal entries for this one transaction.
        Intended to be used after a transaction is created or updated in admin.
        """
        JournalEntry.objects.filter(source_url=self.get_absolute_url()).delete()
        self.create_journalentry()
        Journaler.save_je_batch()
        JournalLiner.save_jeli_batch()

    @classmethod
    def get_unbalanced_journal_entries(cls):
        return cls._unbalanced_journal_entries


class JournalLiner(object):
    __metaclass__ = ABCMeta

    _jeli_batch = list()  # type:List[JournalEntryLineItem]

    # Each journal liner will have its own logic for creating its line items in the specified entry.
    @abstractmethod
    def create_journalentry_lineitems(self, je: JournalEntry):
        raise NotImplementedError

    @classmethod
    def save_jeli_batch(cls):
        created = JournalEntryLineItem.objects.bulk_create(cls._jeli_batch)
        cls._jeli_batch = []

    @classmethod
    def batch_jeli(cls, jeli: JournalEntryLineItem):
        cls._jeli_batch.append(jeli)
        if len(cls._jeli_batch) > 1000:
            cls.save_jeli_batch()
        return jeli


registered_journaler_classes = []  # type: List[Journaler]


def register_journaler():
    """ Registers the given journaler class so that it will participate in bookkeeping """
    def _decorator(journaler_class):
        if not issubclass(journaler_class, Journaler):
            raise ValueError("Registered class must be a Journaler")
        registered_journaler_classes.append(journaler_class)
        return journaler_class
    return _decorator


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# BUDGET
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@register_journaler()
class Budget(Journaler):

    year = models.IntegerField(blank=False, default=date.today().year,
        help_text="The fiscal year during which this budget applies.")

    name = models.CharField(max_length=40, blank=False,
        help_text="Name of the budget.")

    from_acct = models.ForeignKey(Account, null=False, blank=False,
        related_name='from_budget_set',
        on_delete=models.PROTECT,
        help_text="The acct FROM which funds will be transferred.")

    to_acct = models.ForeignKey(Account, null=False, blank=False,
        related_name='to_budget_set',
        on_delete=models.PROTECT,
        help_text="The acct TO which funds will be transferred.")

    for_accts = models.ManyToManyField(Account, blank=True,
        help_text="The account(s) ultimately funded by this budget.")

    amount = models.DecimalField(max_digits=7, decimal_places=2, null=False, blank=False,
        help_text="The amount budgeted for the year.",
        validators=[MinValueValidator(DEC0)])

    def _create_journalentries(self):
        je = JournalEntry(
            when=date(self.year, 1, 1),
            source_url=self.get_absolute_url(),
        )
        je.prebatch(JournalEntryLineItem(
            account=self.from_acct,
            action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
            amount=self.amount,
            description="Budget xfer to {}".format(self.name)
        ))
        je.prebatch(JournalEntryLineItem(
            account=self.to_acct,
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.amount,
            description="Budget contribution"
        ))
        Journaler.batch(je)

    def __str__(self):
        return self.name

    def clean(self):
        pass
        # TODO: Might want to check that accounts are either "Cash" or descendants of "Cash"


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CASH TRANSFERS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@register_journaler()
class CashTransfer(Journaler):  # Started life as a cash xfer but is now a more general acct transfer.

    from_acct = models.ForeignKey(Account, null=False, blank=False,
        related_name='from_xfer_set',
        on_delete=models.PROTECT,
        help_text="The acct FROM which funds were transferred.")

    to_acct = models.ForeignKey(Account, null=False, blank=False,
        related_name='to_xfer_set',
        on_delete=models.PROTECT,
        help_text="The acct TO which funds were transferred.")

    when = models.DateField(null=False, blank=False,
        help_text="Date of the transfer.")

    amount = models.DecimalField(max_digits=7, decimal_places=2, null=False, blank=False,
        help_text="The amount of the transfer.",
        validators=[MinValueValidator(DEC0)])

    why = models.CharField(max_length=80, blank=False,
        help_text="A short explanation of the transfer.")

    def clean(self):
        # REVIEW: Is this constraint too tight from an accounting perspective?
        if self.from_acct.category != self.to_acct.category:
            msg = "Accounts must be in same category but 'From' is {} and 'To' is {}.".format(
                self.from_acct.category_name,
                self.to_acct.category_name
            )
            raise ValidationError(msg)

    def _create_journalentries(self):
        je = JournalEntry(
            when=self.when,
            source_url=self.get_absolute_url(),
        )
        je.prebatch(JournalEntryLineItem(
            account=self.from_acct,
            action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
            amount=self.amount,
            description="Transfer to {}".format(self.to_acct.name)
        ))
        je.prebatch(JournalEntryLineItem(
            account=self.to_acct,
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.amount,
            description = "Transfer from {}".format(self.from_acct.name)
        ))
        Journaler.batch(je)

    class Meta:
        unique_together = ['from_acct', 'to_acct', 'when', 'why']
        verbose_name = "transfer"


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ENTITY - Any person or organization that is not a member.
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Entity(models.Model):

    name = models.CharField(max_length=40, blank=False,
        help_text="Name of person/organization.")

    email = models.EmailField(max_length=40, blank=True,
        help_text="Email address of person/organization.")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Non-Member Entity"
        verbose_name_plural = "Non-Member Entities"
        ordering = ['name']


class EntityNote(Note):

    entity = models.ForeignKey(Entity,
        on_delete=models.CASCADE,  # No point in keeping the note if the entity is gone.
        help_text="The entity to which the note pertains.")

    @property
    def subject(self):
        return self.entity


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# INVOICES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def make_InvoiceBase(help: Dict[str, str]):

    class InvoiceBase(Journaler):

        invoice_date = models.DateField(null=False, blank=False, default=date.today,
            help_text = help["invoice_date"])

        user = models.ForeignKey(User, null=True, blank=True, default=None,
            on_delete=models.SET_NULL,
            help_text=help["user"])

        entity = models.ForeignKey(Entity, null=True, blank=True, default=None,
            on_delete=models.SET_NULL,
            help_text = help["entity"])

        amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
            help_text=help["amount"])

        description = models.TextField(max_length=1024,
            help_text=help["description"])

        def name(self):
            if self.entity is not None:
                return self.entity.name
            else:
                return self.user.username

        @property
        def invoice_number_str(self) -> str:
            return "XIS{0:05d}".format(self.pk)

        def clean(self):

            if self.user is None and self.entity is None:
                raise ValidationError(_("Either user or entity must be specified."))

            if self.user is not None and self.entity is not None:
                raise ValidationError(_("Only one of user or entity can be specified."))

        def dbcheck(self):
            if self.amount != self.checksum():
                raise ValidationError(_("Total of line items must match amount of invoice."))

        class Meta:
            abstract = True

    return InvoiceBase


recv_invoice_help = {
    "invoice_date": "The date on which the invoice was created.",
    "user":         "If a user owes us, specify them here.",
    "entity":       "If some outside person/org owes us, specify them here.",
    "amount":       "The dollar amount we are invoicing them for.",
    "description":  "Description of goods and/or services we delivered to them.",
    "account":      "The revenue account associated with this invoice.",
}


@register_journaler()
class ReceivableInvoice(make_InvoiceBase(recv_invoice_help)):

    send_invoice = models.BooleanField(default=False,
        help_text="(Re)send the invoice via email. Note: Will be sent at night.")

    def checksum(self) -> Decimal:
        """
        :return: The sum total of all line items. Should match self.amount.
        """
        total = Decimal(0.0)
        for lineitem in self.receivableinvoicelineitem_set.all():
            total += lineitem.amount
        return total

    def __str__(self):
        return "${} owed to us by {} as of {}".format(
            self.amount,
            self.name(),
            self.invoice_date)

    def _create_journalentries(self):
        je = JournalEntry(
            when=self.invoice_date,
            source_url=self.get_absolute_url(),
        )
        je.prebatch(JournalEntryLineItem(
            account=Account.get(ACCT_ASSET_RECEIVABLE),
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.amount,
            description="We invoiced [{}]".format(self.name())
        ))
        self.create_lineitems_for(je)
        Journaler.batch(je)


class ReceivableInvoiceNote(Note):

    invoice = models.ForeignKey(ReceivableInvoice,
        on_delete=models.CASCADE,  # No point in keeping the note if the invoice is gone.
        help_text="The invoice to which the note pertains.")

    @property
    def subject(self):
        return self.invoice

payable_invoice_help = {
    "invoice_date": "The date of the invoice.",
    "user":         "If we owe a user, specify them here.",
    "entity":       "If we owe some outside person/org, specify them here.",
    "amount":       "The dollar amount they invoiced.",
    "description":  "Description of goods and/or services we received from them.",
    "account":      "The expense account associated with this invoice.",
}


@register_journaler()
class PayableInvoice(make_InvoiceBase(payable_invoice_help)):

    subject_to_1099 = models.BooleanField(default="False",
        verbose_name="1099",
        help_text="Check if this invoice is subject to 1099-MISC reporting requirements.")

    def checksum(self) -> Decimal:
        """
        :return: The sum total of all line items. Should match self.amount.
        """
        total = Decimal(0.0)
        for lineitem in self.payableinvoicelineitem_set.all():
            total += lineitem.amount
        return total

    def __str__(self):
        return "${} owed to {} as of {}".format(
            self.amount,
            self.name(),
            self.invoice_date)

    def _create_journalentries(self):
        je = JournalEntry(
            when=self.invoice_date,
            source_url=self.get_absolute_url(),
        )
        je.prebatch(JournalEntryLineItem(
            account=Account.get(ACCT_LIABILITY_PAYABLE),
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.amount,
            description="{} invoiced us".format(quote_entity(self.name()))
        ))

        for pili in self.payableinvoicelineitem_set.all():  # type: PayableInvoiceLineItem
            je.prebatch(JournalEntryLineItem(
                account=pili.account,
                action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                amount=pili.amount,
                description=pili.description
            ))

        Journaler.batch(je)


class PayableInvoiceNote(Note):

    invoice = models.ForeignKey(PayableInvoice,
        on_delete=models.CASCADE,  # No point in keeping the note if the invoice is gone.
        help_text="The invoice to which the note pertains.")

    @property
    def subject(self):
        return self.invoice


class InvoiceLineItem(models.Model):

    description = models.CharField(max_length=128, blank=False,
        help_text="A brief description of this line item.")

    delivery_date = models.DateField(null=False, blank=False,
        help_text="The date on which this line item was delivered.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The dollar amount for this line item.")

    account = models.ForeignKey(Account, null=False, blank=False,
        on_delete=models.PROTECT, # Don't allow acct to be deleted if there are invoices pointing to it.
        help_text="The account associated with this line item.")

    class Meta:
        abstract = True


class ReceivableInvoiceLineItem(InvoiceLineItem, JournalLiner):

    inv = models.ForeignKey(ReceivableInvoice, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the larger invoice, so delete if invoice is deleted.
        help_text="The receivable invoice on which this line item appears.")

    def clean(self):
        if self.account is not None:  # Req'd but not guaranteed to set yet.

            if self.account.category is not Account.CAT_REVENUE:
                 raise ValidationError(_("Account chosen must have category REVENUE."))

            if self.account.type is not Account.TYPE_CREDIT:
                raise ValidationError(_("Account chosen must have type CREDIT."))

    def create_journalentry_lineitems(self, je: JournalEntry):
        je.prebatch(JournalEntryLineItem(
            account=self.account,
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.amount
        ))


class PayableInvoiceLineItem(InvoiceLineItem, JournalLiner):

    inv = models.ForeignKey(PayableInvoice, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the larger invoice, so delete if invoice is deleted.
        help_text="The payable invoice on which this line item appears.")

    def clean(self):
        if self.account is not None:  # Req'd but not guaranteed to set yet.

            if self.account.category not in [Account.CAT_EXPENSE, Account.CAT_ASSET]:
                 raise ValidationError(_("Account chosen must have category EXPENSE or ASSET."))

            if self.account.type is not Account.TYPE_DEBIT:
                raise ValidationError(_("Account chosen must have type DEBIT."))

    def create_journalentry_lineitems(self, je: JournalEntry):
        je.prebatch(JournalEntryLineItem(
            account=self.account,
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.amount
        ))


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# SALE (aka Income Transaction in Admin)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@register_journaler()
class Sale(Journaler):

    sale_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="The date on which the sale was made. Best guess if exact date not known.")

    deposit_date = models.DateField(null=True, blank=True, default=None,
        help_text="The date on which the income from this sale was (or will be) deposited.")

    payer_acct = models.ForeignKey(User, null=True, blank=True, default=None,
        on_delete=models.SET_NULL,  # Keep the note even if the user is deleted.
        help_text="It's preferable, but not necessary, to refer to the customer's account.")

    payer_name = models.CharField(max_length=40, blank=True,
        help_text="Name of person who made the payment. Not necessary if account was linked.")

    payer_email = models.EmailField(max_length=40, blank=True,
        help_text="Email address of person who made the payment.")

    PAID_BY_CASH     = "$"
    PAID_BY_CHECK    = "C"
    PAID_BY_SQUARE   = "S"
    PAID_BY_2CO      = "2"
    PAID_BY_WEPAY    = "W"
    PAID_BY_PAYPAL   = "P"
    PAID_BY_GOFUNDME = "G"
    PAID_BY_CHOICES = [
        (PAID_BY_CASH,     "Cash"),
        (PAID_BY_CHECK,    "Check"),
        (PAID_BY_SQUARE,   "Square"),
        (PAID_BY_2CO,      "2Checkout"),
        (PAID_BY_WEPAY,    "WePay"),
        (PAID_BY_PAYPAL,   "PayPal"),
        (PAID_BY_GOFUNDME, "GoFundMe"),
    ]
    payment_method = models.CharField(max_length=1, choices=PAID_BY_CHOICES,
        null=False, blank=False, default=PAID_BY_CASH,
        help_text="The payment method used.")
    payment_method.verbose_name = "Method"

    method_detail = models.CharField(max_length=40, blank=True,
        help_text="Optional detail specific to the payment method. Check# for check payments.")
    method_detail.verbose_name = "Detail"

    total_paid_by_customer = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The full amount paid by the person, including payment processing fee IF CUSTOMER PAID IT.")
    total_paid_by_customer.verbose_name = "Total Paid"

    processing_fee = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, default=0,
        help_text="Payment processor's fee, REGARDLESS OF WHO PAID FOR IT. Zero for cash/check.")
    processing_fee.verbose_name = "Fee"

    FEE_PAID_BY_NOBODY = "N"
    FEE_PAID_BY_CUSTOMER = "C"
    FEE_PAID_BY_US = "U"
    FEE_PAID_CHOICES = [
        (FEE_PAID_BY_NOBODY, "N/A"),
        (FEE_PAID_BY_CUSTOMER, "Customer"),
        (FEE_PAID_BY_US, ORG_NAME),
    ]
    fee_payer = models.CharField(max_length=1, choices=FEE_PAID_CHOICES,
        null=False, blank=False, default=FEE_PAID_BY_US,
        help_text="Who paid the processing fee (if any)?")

    # send_receipt will eventually be obsoleted by modelmailer app. Remove at that time.
    send_receipt = models.BooleanField(default=False,
        help_text="(Re)send a DONATION receipt to the donor. Note: Will send at night.")

    ctrlid = models.CharField(max_length=40, null=False, blank=False, default=next_sale_ctrlid,
        help_text="Payment processor's id for this payment.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually enetered data.")

    def link_to_user(self) -> bool:

        if self.protected:
            return False

        # Attempt to match by EMAIL
        if self.payer_email is not None and len(self.payer_email) > 0:
            try:
                email_matches = User.objects.filter(email=self.payer_email, is_active=True)
                if len(email_matches) == 1:
                    self.payer_acct = email_matches[0]
                    return True
                elif len(email_matches) > 1:
                    logger.warning("Unable to link sale b/c multiple %s emails", self.payer_email)
            except User.DoesNotExist:
                pass

        # Attempt to match by NAME
        nameobj = HumanName(str(self.payer_name))
        fname = nameobj.first
        lname = nameobj.last
        if fname is not None and lname is not None and len(fname+lname) > 0:
            try:
                name_matches = User.objects.filter(
                    first_name__iexact=fname,
                    last_name__iexact=lname,
                    is_active=True,
                )
                if len(name_matches) == 1:
                    self.payer_acct = name_matches[0]
                    return True
                elif len(name_matches) > 1:
                    logger.warning("Unable to link sale b/c multiple %s %s accts", fname, lname)
            except User.DoesNotExist:
                pass
        return False

    class Meta:
        unique_together = ('payment_method', 'ctrlid')
        verbose_name = "Income transaction"

    def checksum(self) -> Decimal:
        """
        :return: The sum total of all expense line items. Should match self.amount.
        """
        total = Decimal(0.0)

        # This is coded generically because the 'books' app doesn't know which models in other
        # apps will point back to a sale. So it looks for fields like "sale_price" and "qty_sold"
        # in all related models.

        # This is the new way to get_all_related_objects
        # per https://docs.djangoproject.com/en/1.10/ref/models/meta/
        related_objects = [
            f for f in self._meta.get_fields()
              if (f.one_to_many or f.one_to_one)
              and f.auto_created
              and not f.concrete
        ]
        link_names = [rel.get_accessor_name() for rel in related_objects]
        for link_name in link_names:
            if link_name in ['salenote_set', 'receivableinvoicereference_set']: continue
            # TODO: Can a select_related or prefetch_related improve performance here?
            line_items = getattr(self, link_name).all()
            for line_item in line_items:
                line_total = Decimal(0.0)
                if hasattr(line_item, 'amount'): line_total += line_item.amount
                elif hasattr(line_item, 'sale_price'): line_total += line_item.sale_price
                if hasattr(line_item, 'qty_sold'): line_total *= (line_item.qty_sold or Decimal('1'))
                total += line_total
        for invref in self.receivableinvoicereference_set.all():
            total += invref.portion if invref.portion is not None else invref.invoice.amount
        return total

    def clean(self):

        # The following is a noncritical constraint, enforced here:
        if self.processing_fee == Decimal(0.00) and self.fee_payer != self.FEE_PAID_BY_NOBODY:
            self.fee_payer = self.FEE_PAID_BY_NOBODY

        if self.deposit_date is not None and self.sale_date is not None \
         and self.deposit_date < self.sale_date:
            raise ValidationError(_("Deposit date cannot be earlier than sale date."))

        if self.payment_method == self.PAID_BY_CHECK \
          and self.method_detail > "" and not self.method_detail.isnumeric():
            raise ValidationError(_("Detail for check payments should only be the bare check number without # or other text."))

        if self.payment_method == self.PAID_BY_CASH and self.method_detail > "":
            raise ValidationError(_("Cash payments shouldn't have detail. Cash is cash."))

    def dbcheck(self):
        sum = self.checksum()
        checksum_matches = sum == self.total_paid_by_customer \
         or sum == self.total_paid_by_customer - self.processing_fee
        if not checksum_matches:
            raise ValidationError(_("Total of line items must match amount transaction."))

    @property
    def payer_str(self) -> Optional[str]:
        if self.payer_name > "":
            return self.payer_name
        elif self.payer_acct is not None:
            return str(self.payer_acct.member)
        elif self.payer_email > "":
            return self.payer_email
        else:
            return None

    def __str__(self):
        payer_str = self.payer_str
        if payer_str is not None:
            return "{} sale to {}".format(self.sale_date, payer_str)
        else:
            return "{} sale to Unk Person".format(self.sale_date)

    def cash_for_item_after_fees(self, item_price: Decimal) -> Decimal:
        if self.fee_payer == self.FEE_PAID_BY_CUSTOMER:
            total_of_item_prices = self.total_paid_by_customer - self.processing_fee
        elif self.fee_payer == self.FEE_PAID_BY_US:
            total_of_item_prices = self.total_paid_by_customer
        else:
            assert self.fee_payer == self.FEE_PAID_BY_NOBODY
            total_of_item_prices = self.total_paid_by_customer

        item_fraction = item_price / total_of_item_prices
        item_share_of_fee = item_fraction * self.processing_fee
        return item_price - item_share_of_fee

    def _create_journalentries(self):
        je = JournalEntry(
            when=self.sale_date,
            source_url=self.get_absolute_url(),
        )
        je.prebatch(JournalEntryLineItem(
            account=Account.get(ACCT_ASSET_CASH),
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.total_paid_by_customer-self.processing_fee,
            description="{} paid us".format(quote_entity(self.payer_str or "unkown"))
        ))
        if self.processing_fee > Decimal(0.00):
            if self.fee_payer == self.FEE_PAID_BY_US:
                je.prebatch(JournalEntryLineItem(
                    account=Account.get(ACCT_EXPENSE_BUSINESS),
                    action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                    amount=self.processing_fee,
                    description="Payment processing fee"
                ))

        self.create_lineitems_for(je)
        Journaler.batch(je)


class SaleLineItem (models.Model):

    sale = models.ForeignKey(Sale,
        on_delete=models.CASCADE,  # No point in keeping the line item if the sale is gone.
        help_text="The sale for which this is a line item.")

    sale_price = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The UNIT price at which this/these item(s) sold.")

    qty_sold = models.IntegerField(null=True, blank=True, default=None,
        help_text="The quantity of the item sold. Leave blank if quantity is not known.")

    class Meta:
        abstract = True


class SaleNote(Note):

    sale = models.ForeignKey(Sale,
        on_delete=models.CASCADE,  # No point in keeping the note if the sale is gone.
        help_text="The sale to which the note pertains.")

    @property
    def subject(self):
        return self.sale


class OtherItemType(models.Model):
    """Cans of soda, bumper stickers, materials, etc."""

    name = models.CharField(max_length=40, unique=True,
        help_text="A short name for the item.")

    description = models.TextField(max_length=1024,
        help_text="A description of the item.")

    # TODO:
    # Revenue acct shouldn't ever be null but needs to temporarily so I can fix up existing entries.
    # Switch to null=False, blank=False, and delete default.
    revenue_acct = models.ForeignKey(Account, null=True, blank=True, default=None,
        on_delete=models.PROTECT,  # Don't allow deletion of acct if item types reference it.
        help_text="The revenue account associated with items of this type.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class OtherItem(models.Model, JournalLiner):

    type = models.ForeignKey(OtherItemType, null=False, blank=False, default=None,
        on_delete=models.PROTECT,  # Don't allow deletion of an item type that appears in a sale.
        help_text="The type of item sold.")

    # Sale related fields: sale, sale_price, qty_sold
    sale = models.ForeignKey(Sale,
        on_delete=models.CASCADE,  # No point in keeping the line item if the sale is gone.
        help_text="The sale for which this is a line item.")

    sale_price = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The UNIT price at which this/these item(s) sold.")

    qty_sold = models.IntegerField(null=True, blank=True, default=None,
        help_text="The quantity of the item sold. Leave blank if quantity is not known.")

    # ETL related fields: sale, sale_price, qty_sol
    ctrlid = models.CharField(max_length=40, null=False, blank=False, unique=True,
        default=next_otheritem_ctrlid,
        help_text="Payment processor's id for this donation, if any.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.")

    def __str__(self):
        return self.type.name

    def create_journalentry_lineitems(self, je: JournalEntry):
        je.prebatch(JournalEntryLineItem(
            account=self.type.revenue_acct,
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.sale_price * (self.qty_sold or Decimal('1')),
            description=self.type.name
        ))


class MonetaryDonationReward(models.Model):

    name = models.CharField(max_length=40, blank=False,
        help_text="Name of the reward.")

    min_donation = models.DecimalField(max_digits=6, decimal_places=2,
        null=False, blank=False, default=Decimal(0.0),
        help_text="The minimum donation required to earn this reward.")

    cost_to_org = models.DecimalField(max_digits=6, decimal_places=2,
        null=False, blank=False, default=Decimal(0.0),
        help_text="The cost of this reward to {}.".format(ORG_NAME))

    fair_mkt_value = models.DecimalField(max_digits=6, decimal_places=2,
        null=False, blank=False, default=Decimal(0.0),
        help_text="The value of this reward to the donor, for tax purposes.")

    description = models.TextField(max_length=1024,
        help_text="Description of the reward.")

    def clean(self):

        if self.cost_to_org > self.min_donation:
            raise ValidationError(_("Min donation should cover the cost of the reward."))

    def __str__(self):
        return self.name


class MonetaryDonation(models.Model, JournalLiner):

    # NOTE: A monetary donation can ONLY appear on a Sale.

    sale = models.ForeignKey(Sale, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the sale so they should be deleted.
        help_text="The sale that includes this line item.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The amount donated.")

    earmark = models.ForeignKey(Account, null=False, blank=False,
        default=ACCT_REVENUE_DONATION,
        on_delete=models.PROTECT,
        limit_choices_to=
            (models.Q(parent_id=ACCT_REVENUE_DONATION)|models.Q(id=ACCT_REVENUE_DONATION))
            & ~
            models.Q(id=ACCT_REVENUE_DISCOUNT),
        help_text="Specify a donation subaccount, when possible.")

    # I'm only doing this so that CampaignAdmin can show MonetaryDonation inlines.
    # It should be safe to delete this 'campaign' field if somebody has a better idea.
    campaign = models.ForeignKey('Campaign', null=True, blank=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text="This is a denormalized field and will be maintained by code.")

    reward = models.ForeignKey(MonetaryDonationReward, null=True, blank=True, default=None,
        on_delete=models.PROTECT,  # Don't allow a reward to be deleted if donations point to it.
        help_text="The reward given to the donor, if any.")

    ctrlid = models.CharField(max_length=40, null=False, blank=False, unique=True,
        default=next_monetarydonation_ctrlid,
        help_text="Payment processor's id for this donation, if any.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.")

    def __str__(self):
        return str("$"+str(self.amount))

    def clean(self):
        donation_root_acct = Account.get(ACCT_REVENUE_DONATION)
        if self.earmark != donation_root_acct:
            if not self.earmark.is_subaccount_of(donation_root_acct):
                msg = "Account chosen must be a subaccount of {}.".format(donation_root_acct.name)
                raise ValidationError({'earmark': [msg]})
        if self.earmark.category is not Account.CAT_REVENUE:
            msg = "Account chosen must have category REVENUE."
            raise ValidationError({'earmark': [msg]})
        if self.earmark.type is not Account.TYPE_CREDIT:
            msg = "Account chosen must have type CREDIT."
            raise ValidationError({'earmark': [msg]})
        # NOTE: self.campaign is set in a signal handler.

    def create_journalentry_lineitems(self, je: JournalEntry):

        je.prebatch(JournalEntryLineItem(
            account=self.earmark,
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            amount=self.amount,
            description="Donation from {}".format(quote_entity(self.sale.payer_str or "unknown"))
        ))

        # If this donation is contributing to a fund raising campaign then
        # shuffle cash from the top-level cash acct to the campaign's cash fund.
        try:
            campaign = self.earmark.campaign_as_revenue  # type: Campaign
            net_donation = self.sale.cash_for_item_after_fees(self.amount)
            if campaign is not None:
                je.prebatch(JournalEntryLineItem(
                    account=Account.get(ACCT_ASSET_CASH),
                    action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
                    amount=net_donation,
                    # Description string must have exactly this form in order to optimize out:
                    description="{} paid us".format(quote_entity(self.sale.payer_str or "unkown"))
                ))
                je.prebatch(JournalEntryLineItem(
                    account=campaign.cash_account,
                    action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                    amount=net_donation,
                    description="Donation from {}".format(quote_entity(self.sale.payer_str or "unknown"))
                ))
        except Campaign.DoesNotExist:
            pass


class ReceivableInvoiceReference(models.Model, JournalLiner):
    sale = models.ForeignKey(Sale, null=False, blank=False,
        on_delete=models.CASCADE,  # Delete this relation if the income transaction is deleted.
        help_text="The income transaction that pays the invoice.")

    # I wanted the following to be OneToOne but there might be multiple partial payments
    # toward a single invoice. I.e. I'm paralleling the ExpenseClaimReference case.
    invoice = models.ForeignKey(ReceivableInvoice, null=False, blank=False,
        on_delete=models.CASCADE,  # Delete this relation if the invoice is deleted.
        help_text="The invoice that is paid by the income transaction.")
    # 'not_part_of', below, indicates that this Reference is not part of the referenced Invoice.
    invoice.is_not_parent = True

    portion = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, default=None,
        help_text="Leave blank unless they're only paying a portion of the invoice.")

    def create_journalentry_lineitems(self, je: JournalEntry):

        whostr = quote_entity(self.invoice.name())

        if self.portion is not None and self.portion < self.invoice.amount:
            amount = self.portion
            desc = "{} partially paid our invoice".format(whostr)
        else:
            amount = self.invoice.amount
            desc = "{} paid our invoice".format(whostr)

        je.prebatch(JournalEntryLineItem(
            account=Account.get(ACCT_ASSET_RECEIVABLE),
            action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
            amount=amount,
            description=desc
        ))


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# FUND RAISING CAMPAIGNS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Campaign(models.Model):

    name = models.CharField(max_length=40, blank=False,
        help_text="Short name of the campaign.")

    is_active = models.BooleanField(default=True,
        help_text="Whether or not this campaign is currently being pursued.")

    target_amount = models.DecimalField(max_digits=7, decimal_places=2, null=False, blank=False,
        help_text="The total amount that needs to be collected in donations.")

    revenue_account = models.OneToOneField(Account, null=False, blank=False,
        related_name='campaign_as_revenue',
        on_delete=models.PROTECT,  # Don't allow deletion of account if campaign still exists.
        help_text="The revenue account used by this campaign.")

    cash_account = models.OneToOneField(Account, null=False, blank=False,
        related_name='campaign_as_cash',
        on_delete=models.PROTECT,  # Don't allow deletion of account if campaign still exists.
        help_text="The cash account used by this campaign.")

    description = models.TextField(max_length=1024,
        help_text="A description of the campaign and why people should donate to it.")

    def clean(self):
        if self.revenue_account is not None:  # Req'd but not guaranteed to set yet.
            if self.revenue_account.category is not Account.CAT_REVENUE:
                 raise ValidationError(_("Account chosen must have category REVENUE."))
            if self.revenue_account.type is not Account.TYPE_CREDIT:
                raise ValidationError(_("Account chosen must have type CREDIT."))
        if self.cash_account is not None:  # Req'd but not guaranteed to set yet.
            if self.cash_account.category is not Account.CAT_ASSET:
                 raise ValidationError(_("Account chosen must have category REVENUE."))
            if self.cash_account.type is not Account.TYPE_DEBIT:
                raise ValidationError(_("Account chosen must have type CREDIT."))

    def __str__(self):
        return self.name


class CampaignNote(Note):

    is_public = models.BooleanField(default=False,
        help_text="Should this note be visible to the public as a campaign update?")

    campaign = models.ForeignKey(Campaign,
        on_delete=models.CASCADE,  # No point in keeping the update if the campaign is deleted.
        help_text="The campaign to which this public update applies.")

    @property
    def subject(self):
        return self.campaign


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# PHYSICAL (NOT MONETARY) DONATIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Donation(models.Model):

    donation_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="The date on which the donation was made. Best guess if exact date not known.")

    donator_acct = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the note even if the user is deleted.
        help_text="It's preferable, but not necessary, to refer to the donator's account.")

    donator_name = models.CharField(max_length=40, blank=True,
        help_text="Name of person who made the donation. Not necessary if account is linked.")

    donator_email = models.EmailField(max_length=40, blank=True,
        help_text="Email address of person who made the donation.")

    # send_receipt will eventually be obsoleted by modelmailer app. Remove at that time.
    send_receipt = models.BooleanField(default=True,
        help_text="(Re)send a receipt to the donor. Note: Will send at night.")

    def __str__(self):
        name = "Anonymous"
        if len(str(self.donator_name)) > 0: name = self.donator_name
        elif self.donator_acct is not None: name = str(self.donator_acct)
        elif len(str(self.donator_email)) > 0: name = self.donator_email
        return "{} on {}".format(name, self.donation_date)

    def clean(self):

        if self.send_receipt:
            if self.donator_acct is None:
                if self.donator_email=="":
                    raise ValidationError(_("No email address for receipt. Link to acct or provide donator email."))
            else:  # donator acct is specified
                if self.donator_acct.email=="" and self.donator_email=="":
                    raise ValidationError(_("No email address for receipt. Please fill the 'donator email' field."))

    def dbcheck(self):
        if len(self.donateditem_set.all()) < 1:
            raise ValidationError(_("Every phyisical donation must include at least one line item."))

    class Meta:
        verbose_name = "Physical donation"


class DonationNote(Note):

    donation = models.ForeignKey(Donation,
        on_delete=models.CASCADE,  # No point in keeping the note if the donation is deleted.
        help_text="The donation to which this note applies.")

    @property
    def subject(self):
        return self.donation


class DonatedItem(models.Model):

    donation = models.ForeignKey(Donation, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the donation so delete them.
        help_text="The donation that includes this line item.")

    value = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The value of the item donated.")

    description = models.TextField(max_length=1024,
        help_text="A description of the item donated.")

    def __str__(self):
        return self.description[:40]


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# EXPENSE CLAIMS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@register_journaler()
class ExpenseClaim(Journaler):

    claimant = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the claim for accounting purposes, even if the user is deleted.
        help_text="The member who wrote this note.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The dollar amount for the entire claim.")

    when_submitted = models.DateField(null=True, blank=True, default=None,
        help_text="The date on which the claim was most recently (re)submitted for reimbursement.")

    submit = models.BooleanField(default=False,
        help_text="(Re)submit the claim for processing and reimbursement.")

    donate_reimbursement = models.BooleanField(default=False,
        help_text="Claimant will not receive a payment. Reimbursement will become a donation.")

    def reimbursed(self) -> Decimal:
        """
        :return: The sum total of all reimbursements.
        """
        total = Decimal(0.0)
        if self.donate_reimbursement:
            total = self.amount
        else:
            for ref in self.expenseclaimreference_set.all():
                if ref.portion is not None:
                    total += ref.portion
                else:
                    total += self.amount
        return total

    def remaining(self) -> Decimal:
        return self.amount - self.reimbursed()

    def status_str(self) -> str:
        if self.remaining() == Decimal(0):
            return "closed"
        if self.when_submitted is not None:
            return "submitted"
        if self.remaining() > Decimal(0):
            return "open"
        return "?"

    def checksum(self) -> Decimal:
        """
        :return: The sum total of all expense line items. Should match self.amount.
        """
        total = Decimal(0.0)
        for lineitem in self.expenselineitem_set.all():
            total += lineitem.amount
            total -= lineitem.discount
        return total

    def __str__(self):
        return "${} for {}".format(self.amount, self.claimant)

    def dbcheck(self):
        if self.amount != self.checksum():
            raise ValidationError(_("Total of line items must match amount of claim."))

    def _create_journalentries(self):

        source_url = self.get_absolute_url()
        name_str = quote_entity(self.claimant.username)
        when = self.when_submitted

        if when is None:
            # Explicitly submitting isn't yet a req'd part of our workflow.
            # As a result, most claims (at time of this writing) don't have a submitted date and never well.
            # This gives us a date that is CLOSE TO the date on which they should have submitted.
            latest_eli = self.expenselineitem_set.latest('expense_date')  # type: ExpenseLineItem
            when = latest_eli.expense_date

        je = JournalEntry(
            when=when,
            source_url=source_url
        )

        if self.donate_reimbursement:
            je.prebatch(JournalEntryLineItem(
                account=Account.get(ACCT_REVENUE_DONATION),
                action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                amount=self.amount,
                description="{} donated an expense claim reimbursment to us".format(name_str)
            ))
        else:
            je.prebatch(JournalEntryLineItem(
                account=Account.get(ACCT_LIABILITY_PAYABLE),
                action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                amount=self.amount,
                description="{} filed an expense claim against us".format(name_str)

            ))

        for eli in self.expenselineitem_set.all():  # type: ExpenseLineItem
            je.prebatch(JournalEntryLineItem(
                account=eli.account,
                action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                amount=eli.amount-eli.discount,
                description=eli.description
            ))

        Journaler.batch(je)


class ExpenseClaimNote(Note):

    claim = models.ForeignKey(ExpenseClaim,
        on_delete=models.CASCADE,  # No point in keeping the note if the claim is gone.
        help_text="The claim to which the note pertains.")

    @property
    def subject(self):
        return self.claim


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# EXPENSE TRANSACTION
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@register_journaler()
class ExpenseTransaction(Journaler):

    payment_date = models.DateField(null=True, blank=True, default=None,
        help_text="The date on which the expense was paid (use bank statement date). Blank if not yet paid or statement not yet received. Best guess if paid but exact date not known.")

    recipient_acct = models.ForeignKey(User, null=True, blank=True, default=None,
        on_delete=models.SET_NULL,  # Keep the transaction even if the user is deleted.
        help_text="If payment was made to a user, speicfy them here.",
        verbose_name="User acct paid")

    recipient_entity = models.ForeignKey(Entity, null=True, blank=True, default=None,
        on_delete=models.SET_NULL,
        help_text="If some outside person/org was paid, specify them here.",
        verbose_name="Entity acct paid")

    # TODO: Once recipient_name and recipient_email data is moved to entities, these two fields should be removed.
    recipient_name = models.CharField(max_length=40, blank=True,
        help_text="Name of person/org paid. Not req'd if an acct was linked, above.",
        verbose_name="Name paid")
    recipient_email = models.EmailField(max_length=40, blank=True,
        help_text="Optional, sometimes useful ",
        verbose_name="Optional email")

    @property
    def recipient_str(self) -> Optional[str]:
        if self.recipient_name > "":
            return self.recipient_name
        elif self.recipient_acct is not None:
            return str(self.recipient_acct.member)
        elif self.recipient_email > "":
            return self.recipient_email
        elif self.recipient_entity is not None:
            return self.recipient_entity.name
        else:
            return None

    amount_paid = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The dollar amount of the payment.")

    PAID_BY_CASH   = "$"
    PAID_BY_CHECK  = "C"
    PAID_BY_XFER   = "X"  # Electronic transfer
    PAID_BY_CHOICES = [
        (PAID_BY_CASH,  "Cash"),
        (PAID_BY_CHECK, "Check"),
        (PAID_BY_XFER,  "Electronic"),
    ]
    payment_method = models.CharField(max_length=1, choices=PAID_BY_CHOICES,
        null=False, blank=False, default=PAID_BY_CASH,
        help_text="The payment method used.")
    payment_method.verbose_name = "Method"

    method_detail = models.CharField(max_length=40, blank=True, null=True,
        help_text="Optional detail specific to the payment method. Check# for check payments.")
    method_detail.verbose_name = "Detail"

    # Can't do the unique constraint because electronic and cash payments don't have detail.
    # class Meta:
    #     unique_together = ('payment_method', 'method_detail')

    def payment_method_verbose(self):
        return dict(ExpenseTransaction.PAID_BY_CHOICES)[self.payment_method]

    def clean(self):
        recip_spec_count = 0
        recip_spec_count += int(self.recipient_acct is not None)
        recip_spec_count += int(self.recipient_entity is not None)
        recip_spec_count += int(self.recipient_name > "")
        if recip_spec_count != 1:
            raise ValidationError(_("Recipient must be specified as EXACTLY ONE of user acct, entity acct, or name/email."))

        if self.payment_method == self.PAID_BY_CHECK \
          and self.method_detail > "" and not self.method_detail.isnumeric():
            raise ValidationError(_("Detail for check payments should only be the bare check number without # or other text."))
          # TODO: Check for duplicate check number here?

        if self.method_detail is not None:
            if self.payment_method == self.PAID_BY_CASH and self.method_detail > "":
                raise ValidationError(_("Cash payments shouldn't have detail. Cash is cash."))

    def checksum(self) -> Decimal:
        """
        :return: The sum total of all line items. Should match self.amount_paid.
        """
        total = Decimal(0.0)
        for lineitem in self.expenselineitem_set.all():
            total += lineitem.amount
            total -= lineitem.discount
        for claimref in self.expenseclaimreference_set.all():
            total += claimref.portion if claimref.portion is not None else claimref.claim.amount
        for payable in self.payableinvoicereference_set.all():
            total += payable.portion if payable.portion is not None else payable.invoice.amount
        return total

    def dbcheck(self):
        if  self.amount_paid != self.checksum():
            raise ValidationError(_("Total of line items must match amount of transaction."))

    def __str__(self):
        return "${} by {}".format(self.amount_paid, self.payment_method_verbose())

    def _create_journalentries(self):
        je = JournalEntry(
            when=self.payment_date,
            source_url=self.get_absolute_url()
        )

        self.create_lineitems_for(je)

        # Run through the line items creating cash/expense entries.
        for eli in self.expenselineitem_set.all():

            je.prebatch(JournalEntryLineItem(
                account=get_cashacct_for_expenseacct(eli.account, je.when.year),
                action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
                amount=eli.amount - eli.discount,
                description="We paid {}".format(quote_entity(self.recipient_str))
            ))
            je.prebatch(JournalEntryLineItem(
                account=Account.get(ACCT_REVENUE_DISCOUNT),
                action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                amount=eli.discount,
                description="{} donated by discount".format(quote_entity(self.recipient_str))
            ))
            je.prebatch(JournalEntryLineItem(
                account=eli.account,
                action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                amount=eli.amount,
                description=eli.description
            ))

        Journaler.batch(je)


# REVIEW:
def get_cashacct_for_expenseacct(expenseacct: Account, transaction_year: int) -> Account:

    budgets = expenseacct.budget_set.filter(year=transaction_year)  # type: List[Budget]
    if len(budgets) > 1:
        budget_names = list(map(lambda x: x.name, budgets))
        logger.error("%s has too many active budgets: %s", expenseacct, str(budget_names))
    if len(budgets) == 1:
        budget = budgets[0]  # type: Budget
        assert budget is not None
        return budget.to_acct
    else:
        return Account.get(ACCT_ASSET_CASH)


class ExpenseClaimReference(models.Model, JournalLiner):

    exp = models.ForeignKey(ExpenseTransaction, null=False, blank=False,
        on_delete=models.CASCADE,  # Delete this relation if the expense transaction is deleted.
        help_text="The expense transaction that pays the claim.")

    # I wanted the following to be OneToOne but there is at least one case of multiple partial
    # reimbursements for a single claim.
    claim = models.ForeignKey(ExpenseClaim, null=False, blank=False,
        on_delete=models.CASCADE,  # Delete this relation if the claim is deleted.
        help_text="The claim that is paid by the expense transaction.")

    portion = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, default=None,
        help_text="Leave blank unless you're only paying a portion of the claim.")

    def create_journalentry_lineitems(self, je: JournalEntry):

        uname = quote_entity(self.claim.claimant.username)
        if self.portion is not None and self.portion < self.claim.amount:
            desc = "We partially paid {}'s expense claim".format(uname)
            amount = self.portion
        else:
            desc = "We paid {}'s expense claim".format(uname)
            amount = self.claim.amount

        je.prebatch(JournalEntryLineItem(
            account=Account.get(ACCT_LIABILITY_PAYABLE),
            action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
            amount=amount,
            description=desc
        ))

        for eli in self.claim.expenselineitem_set.all():  # type: ExpenseLineItem

            who_paid = self.claim.claimant.username

            factor = float(amount) / float(self.claim.amount)  # type: float
            portion_flt = factor * float(eli.amount)  # type: float
            portion_dec = Decimal.from_float(round(portion_flt, 2))  # type: Decimal
            discount_flt = factor * float(eli.discount)  # type: float
            discount_dec = Decimal.from_float(round(discount_flt, 2))  # type: Decimal

            je.prebatch(JournalEntryLineItem(
                account=get_cashacct_for_expenseacct(eli.account, je.when.year),
                action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
                amount=portion_dec,
                description="We paid {}".format(quote_entity(who_paid))
            ))

            if eli.discount > DEC0:  # Note, this is for CHARITABLE discounts against goods or services.
                je.prebatch(JournalEntryLineItem(
                    account=Account.get(ACCT_REVENUE_DISCOUNT),
                    action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
                    amount=discount_dec,
                ))



class ExpenseLineItem(models.Model):

    # An expense line item can appear in an ExpenseClaim or in an ExpenseTransaction

    claim = models.ForeignKey(ExpenseClaim, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the larger claim, so delete if claim is deleted.
        help_text="The claim on which this line item appears.")

    exp = models.ForeignKey(ExpenseTransaction, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the larger transaction, so delete if transaction is deleted.
        help_text="The expense transaction on which this line item appears.")

    bought_from = models.ForeignKey(Entity, null=True, blank=True, default=None,
        on_delete=models.PROTECT,  # Don't want to allow entity to be deleted if it's in use.
        help_text="Who was this purchased from (optional).")

    description = models.CharField(max_length=80, blank=False,
        help_text="A brief description of this line item.")

    expense_date = models.DateField(null=False, blank=False,
        help_text="The date on which the expense was incurred.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The dollar amount for this line item BEFORE any discount.")

    discount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, default=0.00,
        help_text="Any CHARITABLE discount applied to this purchase.")

    account = models.ForeignKey(Account, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the larger claim, so delete if claim is deleted.
        limit_choices_to=
            (models.Q(category=Account.CAT_EXPENSE) | models.Q(category=Account.CAT_ASSET))
            & ~
            (models.Q(parent_id=ACCT_ASSET_CASH) | models.Q(id=ACCT_ASSET_CASH)),
        help_text="The account against which this line item is claimed, e.g. 'Wood Shop', '3D Printers'.")

    receipt_num = models.IntegerField(null=True, blank=True,
        help_text="The receipt number assigned by the treasurer and written on the receipt.")

    approved_by = models.ForeignKey(User, null=True, blank=True, default=None,
        on_delete=models.SET_NULL,  # If user is deleted, just null this out.
        help_text="Usually the shop/account manager. Leave blank if not yet approved.")

    def __str__(self):
        return "${} on {}".format(self.amount, self.expense_date)

    def _check_acct(self):
        if self.account is not None:  # Req'd but not guaranteed to be set yet.
            if self.account.category not in [Account.CAT_EXPENSE, Account.CAT_ASSET]:
                raise ValidationError(_("Account chosen must have category EXPENSE or ASSET."))
            if self.account.is_subaccount_of(Account.get(ACCT_ASSET_CASH)):
                raise ValidationError({'account':[_("Cannot expense against a cash account. You probably want a 'supplies', 'maintenance', or 'equipment' account, instead.")]})

    def clean(self):
        self._check_acct()

    def dbcheck(self):
        # Relationships can't be checked in clean but can be checked later in a "db check" operation.
        if self.claim is None and self.exp is None:
            raise ValidationError(_("Expense line item must be part of a claim or transaction."))
        self._check_acct()


class ExpenseTransactionNote(Note):

    exp = models.ForeignKey(ExpenseTransaction,
        on_delete=models.CASCADE,  # No point in keeping the note if the transaction is gone.
        help_text="The expense transaction to which the note pertains.")

    @property
    def subject(self):
        return self.exp


class PayableInvoiceReference(models.Model, JournalLiner):

    exp = models.ForeignKey(ExpenseTransaction, null=False, blank=False,
        on_delete=models.CASCADE,  # Delete this relation if the expense transaction is deleted.
        help_text="The expense transaction by which we pay the invoice.")

    # I wanted the following to be OneToOne but there might be multiple partial payments
    # toward a single invoice. I.e. I'm paralleling the ExpenseClaimReference case.
    invoice = models.ForeignKey(PayableInvoice, null=False, blank=False,
        on_delete=models.CASCADE,  # Delete this relation if the invoice is deleted.
        help_text="The invoice that is paid by the expense transaction.")
    # 'not_part_of', below, indicates that this Reference is not part of the referenced Invoice.
    invoice.is_not_parent = True

    portion = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, default=None,
        help_text="Leave blank unless we're only paying a portion of the invoice.")

    def create_journalentry_lineitems(self, je: JournalEntry):

        name_str = quote_entity(self.invoice.name())
        if self.portion is not None and self.portion < self.invoice.amount:
            desc = "We partially paid {}'s invoice".format(name_str)
            amount = self.portion
        else:
            desc = "We paid {}'s invoice".format(name_str)
            amount = self.invoice.amount

        je.prebatch(JournalEntryLineItem(
            account=Account.get(ACCT_LIABILITY_PAYABLE),
            action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
            amount=amount,
            description=desc
        ))

        for pili in self.invoice.payableinvoicelineitem_set.all():  # type: PayableInvoiceLineItem

            factor = float(amount) / float(self.invoice.amount)  # type: float
            portion_flt = factor * float(pili.amount)  # type: float
            portion_dec = Decimal.from_float(round(portion_flt, 2))  # type: Decimal

            je.prebatch(JournalEntryLineItem(
                account=get_cashacct_for_expenseacct(pili.account, je.when.year),
                action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
                amount=portion_dec,
                description=desc
            ))


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# BANK ACCOUNTS AND THEIR BALANCES (for comparison with and audit of books)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class BankAccount(models.Model):

    name = models.CharField(max_length=40, unique=True,
        help_text="A short name for the bank account.")

    description = models.TextField(max_length=1024,
        help_text="A description of the bank account, the reason it exists, etc.")

    def __str__(self):
        return self.name


class BankAccountBalance(models.Model):

    bank_account = models.ForeignKey(BankAccount, null=False, blank=False,
        on_delete=models.PROTECT,
        help_text="The account with this balance."
    )

    when = models.DateField(null=False, blank=False,
        help_text="The date on which the balance was recorded.")

    balance = models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False,
        help_text="The dollar balance on the given date.")

    order_on_date = models.IntegerField(default=0, blank=False,
        help_text="0 indicates end-of-day! Earlier entries must be negative.",
        validators=[MaxValueValidator(0)])

    class Meta:
        unique_together = ['bank_account', 'when', 'order_on_date']
