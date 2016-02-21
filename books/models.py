from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
        # This only happens for a new database when there are no physical paid memberships.
        return "0".zfill(6)


class Sale(models.Model):

    sale_date = models.DateField(null=False, blank=False, default=timezone.now,
        help_text="The date on which the sale was made. Best guess if exact date not known.")

    payer_name = models.CharField(max_length=40, blank=True,
        help_text="Name of person who made the payment.")

    payer_email = models.EmailField(max_length=40, blank=True,
        help_text="Email address of person who made the payment.")

    PAID_BY_CASH   = "$"
    PAID_BY_CHECK  = "C"
    PAID_BY_GIFT   = "G"
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

    total_paid_by_customer = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The full amount paid by the person, including payment processing fee IF CUSTOMER PAID IT.")
    total_paid_by_customer.verbose_name = "Total Paid"

    processing_fee = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, default=0,
        help_text="Payment processor's fee, REGARDLESS OF WHO PAID FOR IT. Zero for cash/check.")
    processing_fee.verbose_name = "Fee"

    ctrlid = models.CharField(max_length=40, null=False, blank=False, default=next_sale_ctrlid,
        help_text="Payment processor's id for this payment.")

    class Meta:
        unique_together = ('payment_method', 'ctrlid')


class SaleNote(models.Model):

    # Note will become anonymous if author is deleted or author is blank.
    author = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the note even if the member is deleted.
        help_text="The member who wrote this note.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the sale.")

    purchase = models.ForeignKey(Sale,
        on_delete=models.PROTECT)  # Don't want accounting-related info deleted


class SaleLineItem(models.Model):

    sale = models.ForeignKey(Sale, null=True, blank=True,
        on_delete=models.PROTECT,  # Don't delete accounting info.
        help_text="The sale that includes this line item.")

    class Meta:
        abstract = True

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# DONATIONS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Donation(models.Model):

    donation_date = models.DateField(null=False, blank=False, default=timezone.now,
        help_text="The date on which the donation was made. Best guess if exact date not known.")

    donator_name = models.CharField(max_length=40, blank=True,
        help_text="Name of person who made the donation.")

    donator_email = models.EmailField(max_length=40, blank=True,
        help_text="Email address of person who made the donation.")


class DonationNote(models.Model):

    # Note will become anonymous if author is deleted or author is blank.
    author = models.ForeignKey(User, null=True, blank=True,
        on_delete=models.SET_NULL,  # Keep the note even if the member is deleted.
        help_text="The member who wrote this note.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the sale.")

    donation = models.ForeignKey(Donation,
        on_delete=models.PROTECT)  # Don't want accounting-related info deleted


class DonationLineItem(models.Model):

    donation = models.ForeignKey(Donation, null=True, blank=True,
        on_delete=models.PROTECT,  # Don't delete accounting info.
        help_text="The donation that includes this line item.")

    class Meta:
        abstract = True


class MonetaryDonation(DonationLineItem):

    amount = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The amount donated.")


class PhysicalDonation(DonationLineItem):

    value = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The value of the item donated.")

    description = models.TextField(max_length=1024,
        help_text="A description of the item donated.")
