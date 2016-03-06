from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


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

def next_monetarydonation_ctrlid() -> str:

    """Provides an arbitrary default value for the ctrlid field, necessary when data is being entered manually."""

    # REVIEW: There is a nonzero probability that default ctrlids will collide when two users are doing manual data
    # entry at the same time.  This isn't considered a significant problem since we'll be lucky to get ONE person to
    # do data entry. If it does become a problem, the probability could be reduced by using random numbers.

    GEN_CTRLID_PFX = "GEN:"  # The prefix for generated ctrlids.

    # try:
    #    latest_mship = MonetaryDonation.objects.filter(ctrlid__startswith=GEN_CTRLID_PFX).latest('ctrlid')
    #    latest_ctrlid_num = int(latest_mship.ctrlid.replace(GEN_CTRLID_PFX,""))
    #    return GEN_CTRLID_PFX+str(latest_ctrlid_num+1).zfill(6)
    # except MonetaryDonation.DoesNotExist:
    #     # This only happens for a new database when there are no monetary donations with generated ctrlids.
    #     return GEN_CTRLID_PFX+("0".zfill(6))


def next_sale_ctrlid():
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


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# SALE
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Sale(models.Model):

    sale_date = models.DateField(null=False, blank=False, default=timezone.now,
        help_text="The date on which the sale was made. Best guess if exact date not known.")

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

    class Meta:
        unique_together = ('payment_method', 'ctrlid')


class SaleNote(Note):

    sale = models.ForeignKey(Sale,
        on_delete=models.CASCADE,  # No point in keeping the note if the sale is gone.
        help_text="The sale to which the note pertains.")


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# DONATIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Donation(models.Model):

    donation_date = models.DateField(null=False, blank=False, default=timezone.now,
        help_text="The date on which the donation was made. Best guess if exact date not known.")

    donator_acct = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the note even if the user is deleted.
        help_text="It's preferable, but not necessary, to refer to the donator's account.")

    donator_name = models.CharField(max_length=40, blank=True,
        help_text="Name of person who made the donation. Not necessary if account is linked.")

    donator_email = models.EmailField(max_length=40, blank=True,
        help_text="Email address of person who made the donation.")

    def __str__(self):
        name = "Anonymous"
        if len(self.donator_name) > 0: name = self.donator_name
        elif self.donator_acct is not None: name = str(self.donator_acct)
        elif len(self.donator_email) > 0: name = self.donator_email
        return "{} on {}".format(name, self.donation_date)


class DonationNote(Note):

    donation = models.ForeignKey(Donation,
        on_delete=models.CASCADE,  # No point in keeping the note if the donation is deleted.
        help_text="The donation to which this note applies.")


class MonetaryDonation(models.Model):

    # NOTE: A monetary donation can appear on a Donation XOR an Expense Claim XOR a Sale.

    donation = models.ForeignKey(Donation, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the donation so delete them.
        help_text="The donation that includes this line item.")

    sale = models.ForeignKey(Sale, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the sale so they should be deleted.
        help_text="The sale that includes this line item.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The amount donated.")

    ctrlid = models.CharField(max_length=40, null=False, blank=False, unique=True,
        default=next_monetarydonation_ctrlid,
        help_text="Payment processor's id for this donation, if any.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.")

    def clean(self):
        link_count = 0
        if self.donation is not None: link_count += 1
        if self.claim    is not None: link_count += 1
        if self.sale     is not None: link_count += 1
        # Unfortunately, this check doesn't work because of when the admin module links vs calls clean.
        # if link_count == 0:
        #     raise ValidationError(_("A monetary donation cannot stand alone. It must be linked into a transaction."))
        if link_count > 1:
            raise ValidationError(_("A given monetary donation cannot be part of several transactions."))

    def __str__(self):
        return str("$"+str(self.amount))


class PhysicalDonation(models.Model):

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
# EXPENSE CLAIMS & REIMBURSEMENT
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ExpenseClaim(models.Model):

    claim_date = models.DateField(null=False, blank=False, default=timezone.now,
        help_text="The date on which the claim was filed. Best guess if exact date not known.")

    claimant = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the claim for accounting purposes, even if the user is deleted.
        help_text="The member who wrote this note.")

    def __str__(self):
        return "{} {}".format(self.claimant, self.claim_date)


class ExpenseClaimNote(Note):

    claim = models.ForeignKey(ExpenseClaim,
        on_delete=models.CASCADE,  # No point in keeping the note if the claim is gone.
        help_text="The claim to which the note pertains.")


class ExpenseClaimLineItem(models.Model):

    claim = models.ForeignKey(ExpenseClaim, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the larger claim, so delete if claim is deleted.
        help_text="The claim on which this line item appears.")

    description = models.CharField(max_length=80, blank=True,
        help_text="A brief description of this line item.")

    expense_date = models.DateField(null=False, blank=False,
        help_text="The date on which the expense was incurred, from the receipt.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The dollar amount for this line item, from the receipt.")

    account = models.ForeignKey(Account, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the larger claim, so delete if claim is deleted.
        help_text="The account against which this line item is claimed, e.g. 'Wood Shop', '3D Printers'.")

    def __str__(self):
        return "${} on {}".format(self.amount, self.expense_date)


class MonetaryReimbursement(models.Model):

    claim = models.ForeignKey(ExpenseClaim, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the larger claim, so delete if claim is deleted.
        help_text="The claim on which this reimbursement appears.")

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The dollar amount reimbursed.")

    PAID_BY_CASH   = "$"
    PAID_BY_CHECK  = "C"
    PAID_BY_CHOICES = [
        (PAID_BY_CASH,   "Cash"),
        (PAID_BY_CHECK,  "Check"),
    ]
    payment_method = models.CharField(max_length=1, choices=PAID_BY_CHOICES,
        null=False, blank=False, default=PAID_BY_CASH,
        help_text="The payment method used.")
    payment_method.verbose_name = "Method"

    method_detail = models.CharField(max_length=40, blank=True,
        help_text="Optional detail specific to the payment method. Check# for check payments.")
    method_detail.verbose_name = "Detail"

    def payment_method_verbose(self):
        return dict(MonetaryReimbursement.PAID_BY_CHOICES)[self.payment_method]

    def __str__(self):
        return "${} by {}".format(self.amount, self.payment_method_verbose())