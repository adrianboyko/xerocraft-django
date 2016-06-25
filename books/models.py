# pylint: disable=C0330

# Standard
from datetime import date
from decimal import Decimal

# Third party
from django.db import models
from django.db.migrations.recorder import MigrationRecorder
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from nameparser import HumanName

# Local


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

# REVIEW: Is there a way to make a generic next_ctrlid(models.Model)?

# REVIEW: There is a nonzero probability that default ctrlids will collide when two users are doing manual data
# entry at the same time.  This isn't considered a significant problem since we'll be lucky to get ONE person to
# do data entry. If it does become a problem, the probability could be reduced by using random numbers.

GEN_CTRLID_PFX = "GEN:"  # The prefix for generated ctrlids.

def next_monetarydonation_ctrlid() -> str:

    """Provides an arbitrary default value for the ctrlid field, necessary when data is being entered manually."""

    # This method can't calc a ctrlid before ctrlid col is in db, i.e. before migration 0015.
    # Returning an arbitrary string guards against failure during creation of new database, e.g. during tests.
    migs = MigrationRecorder.Migration.objects.filter(app='books', name="0015_auto_20160304_2237")
    if len(migs) == 0: return "arbitrarystring"

    try:
       latest_md = MonetaryDonation.objects.filter(ctrlid__startswith=GEN_CTRLID_PFX).latest('ctrlid')
       latest_ctrlid_num = int(latest_md.ctrlid.replace(GEN_CTRLID_PFX,""))
       return GEN_CTRLID_PFX+str(latest_ctrlid_num+1).zfill(6)
    except MonetaryDonation.DoesNotExist:
        # This only happens for a new database when there are no monetary donations with generated ctrlids.
        return GEN_CTRLID_PFX+("0".zfill(6))


def next_sale_ctrlid() -> str:
    '''Provides an arbitrary default value for the ctrlid field, necessary when check, cash, or gift-card data is being entered manually.'''
    # REVIEW: There is a nonzero probability that default ctrlids will collide when two users are doing manual data entry at the same time.
    #         This isn't considered a significant problem since we'll be lucky to get ONE person to do data entry.
    #         If it does become a problem, the probability could be reduced by using random numbers.
    physical_pay_methods = [
        Sale.PAID_BY_CASH,
        Sale.PAID_BY_CHECK,
    ]
    physical_count = Sale.objects.filter(payment_method__in=physical_pay_methods).count()
    if physical_count > 0:
        latest_pm = Sale.objects.filter(payment_method__in=physical_pay_methods).latest('ctrlid')
        return str(int(latest_pm.ctrlid)+1).zfill(6)
    else:
        # This only happens for a new database when there are no sales with physical payment methods.
        return "0".zfill(6)


def next_otheritem_ctrlid() -> str:

    """Provides an arbitrary default value for the ctrlid field, necessary when data is being entered manually."""

    try:
        # NOTE: This version uses prev created PKs instead of prev created ctrlids.
        # This elminates the need for complicated three-part migrations and MigrationRecorder checks.
        # This may have problems if PKs are reused but they're not in Django + PostgreSQL.
        latest_gcr = OtherItem.objects.latest('id')
        return GEN_CTRLID_PFX+str(int(latest_gcr.id)+1).zfill(6)
    except OtherItem.DoesNotExist:
        # This only happens for a new database when there are no physical paid memberships.
        return GEN_CTRLID_PFX+("0".zfill(6))


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Note
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Note(models.Model):

    author = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the note even if the user is deleted.
        help_text="The user who wrote this note.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the item on which this note appears.")

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

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# SALE
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Sale(models.Model):

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

    PAID_BY_CASH   = "$"
    PAID_BY_CHECK  = "C"
    PAID_BY_SQUARE = "S"
    PAID_BY_2CO    = "2"
    PAID_BY_WEPAY  = "W"
    PAID_BY_PAYPAL = "P"
    PAID_BY_CHOICES = [
        (PAID_BY_CASH,   "Cash"),
        (PAID_BY_CHECK,  "Check"),
        (PAID_BY_SQUARE, "Square"),
        (PAID_BY_2CO,    "2Checkout"),
        (PAID_BY_WEPAY,  "WePay"),
        (PAID_BY_PAYPAL, "PayPal"),
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

    ctrlid = models.CharField(max_length=40, null=False, blank=False, default=next_sale_ctrlid,
        help_text="Payment processor's id for this payment.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually enetered data.")

    def link_to_user(self):

        if self.protected:
            return

        # Attempt to match by EMAIL
        try:
            email_matches = User.objects.filter(email=self.payer_email)
            if len(email_matches) == 1:
                self.payer_acct = email_matches[0]
        except User.DoesNotExist:
            pass

        # Attempt to match by NAME
        nameobj = HumanName(str(self.payer_name))
        fname = nameobj.first
        lname = nameobj.last
        try:
            name_matches = User.objects.filter(first_name__iexact=fname, last_name__iexact=lname)
            if len(name_matches) == 1:
                self.payer_acct = name_matches[0]
            # TODO: Else log WARNING (or maybe just INFO)
        except User.DoesNotExist:
            pass

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
        link_names = [rel.get_accessor_name() for rel in self._meta.get_all_related_objects()]
        for link_name in link_names:
            if link_name in ['salenote_set']: continue
            # TODO: Can a select_related or prefetch_related improve performance here?
            line_items = getattr(self, link_name).all()
            for line_item in line_items:
                line_total = Decimal(0.0)
                if hasattr(line_item, 'amount'): line_total += line_item.amount
                elif hasattr(line_item, 'sale_price'): line_total += line_item.sale_price
                if hasattr(line_item, 'qty_sold'): line_total *= line_item.qty_sold
                total += line_total
        return total

    def clean(self):
        if self.deposit_date is not None and self.sale_date is not None \
         and self.deposit_date < self.sale_date:
            raise ValidationError(_("Deposit date cannot be earlier than sale date."))

    def dbcheck(self):
        sum = self.checksum()
        checksum_matches = sum == self.total_paid_by_customer \
         or sum == self.total_paid_by_customer - self.processing_fee
        if not checksum_matches:
            raise ValidationError(_("Total of line items must match amount transaction."))

    def __str__(self):
        if self.payer_name is not "": return "{} sale to {}".format(self.sale_date, self.payer_name)
        elif self.payer_acct is not None: return "{} sale to {}".format(self.sale_date, self.payer_acct)
        elif self.payer_email is not None: return "{} sale to {}".format(self.sale_date, self.payer_email)
        else: return "{} sale".format(self.sale_date)


class SaleNote(Note):

    sale = models.ForeignKey(Sale,
        on_delete=models.CASCADE,  # No point in keeping the note if the sale is gone.
        help_text="The sale to which the note pertains.")


class OtherItemType(models.Model):
    """Cans of soda, bumper stickers, materials, etc."""

    name = models.CharField(max_length=40, unique=True,
        help_text="A short name for the item.")

    description = models.TextField(max_length=1024,
        help_text="A description of the item.")

    def __str__(self):
        return self.name


class OtherItem(models.Model):

    type = models.ForeignKey(OtherItemType, null=False, blank=False, default=None,
        on_delete=models.PROTECT,  # Don't allow deletion of an item type that appears in a sale.
        help_text="The type of item sold.")

    # Sale related fields: sale, sale_price, qty_sold
    sale = models.ForeignKey(Sale,
        on_delete=models.CASCADE,  # No point in keeping the line item if the sale is gone.
        help_text="The sale for which this is a line item.")

    sale_price = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The UNIT price at which this/these item(s) sold.")

    qty_sold = models.IntegerField(null=False, blank=False, default=1,
        help_text="The quantity of the item sold.")

    # ETL related fields: sale, sale_price, qty_sol
    ctrlid = models.CharField(max_length=40, null=False, blank=False, unique=True,
        default=next_otheritem_ctrlid,
        help_text="Payment processor's id for this donation, if any.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.")

    def __str__(self):
        return self.type.name


class MonetaryDonation(models.Model):

    # NOTE: A monetary donation can ONLY appear on a Sale.

    sale = models.ForeignKey(Sale, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the sale so they should be deleted.
        help_text="The sale that includes this line item.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The amount donated.")

    ctrlid = models.CharField(max_length=40, null=False, blank=False, unique=True,
        default=next_monetarydonation_ctrlid,
        help_text="Payment processor's id for this donation, if any.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.")

    def __str__(self):
        return str("$"+str(self.amount))


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

class ExpenseClaim(models.Model):

    claimant = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the claim for accounting purposes, even if the user is deleted.
        help_text="The member who wrote this note.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The dollar amount for the entire claim.")

    when_submitted = models.DateField(null=True, blank=True, default=None,
        help_text="The date on which the claim was most recently (re)submitted for reimbursement.")

    submit = models.BooleanField(default=False,
        help_text="(Re)submit the claim for processing and reimbursement.")

    def reimbursed(self) -> Decimal:
        """
        :return: The sum total of all reimbursements.
        """
        total = Decimal(0.0)
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
        return total

    # def is_reimbursed(self):
    #     """
    #     :return: True if claim has been reimbursed
    #     """
    #     return len(self.expenseclaimreference_set.all()) > 0
    # is_reimbursed.boolean = True

    def __str__(self):
        return "${} for {}".format(self.amount, self.claimant)

    def dbcheck(self):
        if  self.amount != self.checksum():
            raise ValidationError(_("Total of line items must match amount of claim."))


class ExpenseClaimNote(Note):

    claim = models.ForeignKey(ExpenseClaim,
        on_delete=models.CASCADE,  # No point in keeping the note if the claim is gone.
        help_text="The claim to which the note pertains.")


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# EXPENSE TRANSACTION
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ExpenseTransaction(models.Model):

    payment_date = models.DateField(null=True, blank=True, default=None,
        help_text="The date on which the expense was paid (use bank statement date). Blank if not yet paid or statement not yet received. Best guess if paid but exact date not known.")

    recipient_acct = models.ForeignKey(User, null=True, blank=True, default=None,
        on_delete=models.SET_NULL,  # Keep the note even if the user is deleted.
        help_text="If payment was made to a member, specify them here.")

    recipient_name = models.CharField(max_length=40, blank=True,
        help_text="Name of person/organization paid. Not req'd if account was linked, above.")

    recipient_email = models.EmailField(max_length=40, blank=True,
        help_text="Email address of person/organization paid.")

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

    method_detail = models.CharField(max_length=40, blank=True,
        help_text="Optional detail specific to the payment method. Check# for check payments.")
    method_detail.verbose_name = "Detail"

    def payment_method_verbose(self):
        return dict(ExpenseTransaction.PAID_BY_CHOICES)[self.payment_method]

    def checksum(self) -> Decimal:
        """
        :return: The sum total of all line items. Should match self.amount_paid.
        """
        total = Decimal(0.0)
        for lineitem in self.expenselineitem_set.all():
            total += lineitem.amount
        for claimref in self.expenseclaimreference_set.all():
            total += claimref.portion if claimref.portion is not None else claimref.claim.amount
        return total


    def dbcheck(self):
        if  self.amount_paid != self.checksum():
            raise ValidationError(_("Total of line items must match amount of transaction."))

    def __str__(self):
        return "${} by {}".format(self.amount_paid, self.payment_method_verbose())


class ExpenseClaimReference(models.Model):

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


class ExpenseLineItem(models.Model):

    # An expense line item can appear in an ExpenseClaim or in an ExpenseTransaction

    claim = models.ForeignKey(ExpenseClaim, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the larger claim, so delete if claim is deleted.
        help_text="The claim on which this line item appears.")

    exp = models.ForeignKey(ExpenseTransaction, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the larger transaction, so delete if transaction is deleted.
        help_text="The expense transaction on which this line item appears.")

    description = models.CharField(max_length=80, blank=False,
        help_text="A brief description of this line item.")

    expense_date = models.DateField(null=False, blank=False,
        help_text="The date on which the expense was incurred.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The dollar amount for this line item.")

    account = models.ForeignKey(Account, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the larger claim, so delete if claim is deleted.
        help_text="The account against which this line item is claimed, e.g. 'Wood Shop', '3D Printers'.")

    receipt_num = models.IntegerField(null=True, blank=True,
        help_text="The receipt number assigned by the treasurer and written on the receipt.")

    approved_by = models.ForeignKey(User, null=True, blank=True, default=None,
        help_text="Usually the shop/account manager. Leave blank if not yet approved.")

    def __str__(self):
        return "${} on {}".format(self.amount, self.expense_date)

    def dbcheck(self):
        # Relationships can't be checked in clean but can be checked later in a "db check" operation.
        if self.claim is None and self.exp is None:
            raise ValidationError(_("Expense line item must be part of a claim or transaction."))


class ExpenseTransactionNote(Note):

    exp = models.ForeignKey(ExpenseTransaction,
        on_delete=models.CASCADE,  # No point in keeping the note if the transaction is gone.
        help_text="The expense transaction to which the note pertains.")

