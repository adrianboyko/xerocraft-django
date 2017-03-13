# Standard
from datetime import date

# Third party
from django.core.management.base import BaseCommand, CommandError

# Local
from books.models import (
    Donation, DonationNote,
    Sale, SaleNote,
    ReceivableInvoice, ReceivableInvoiceNote,
)

from books.mailviews import (
    PhysicalDonationMailView,
    CashDonationMailView,
    ReceivableInvoiceMailView,
)

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Email receipts queued up during the day."

    @staticmethod
    def send_physical_donation_receipts():
        mv = PhysicalDonationMailView()
        for donation in Donation.objects.filter(send_receipt=True).all():
            try:
                sent = mv.send(donation)
                if sent:
                    donation.send_receipt = False
                    donation.save()
                    DonationNote.objects.create(donation=donation, author=None,
                        content="Receipt for donated items emailed on {}.".format(date.today().isoformat())
                    )
            except RuntimeWarning as e:
                failure_msg = "Tried to email receipt on {} but failed because:\n{}."
                DonationNote.objects.create(donation=donation, author=None,
                    content=failure_msg.format(date.today().isoformat(), str(e))
                )

    @staticmethod
    def send_monetary_donation_receipts():
        mv = CashDonationMailView()
        for sale in Sale.objects.filter(send_receipt=True).all():
            try:
                if sale.monetarydonation_set.count() == 0:
                    # Protect against case where admin checked the "send DONATION receipt" box but there aren't any donations.
                    continue
                sent = mv.send(sale)
                if sent:
                    sale.send_receipt = False
                    sale.save()
                    SaleNote.objects.create(sale=sale, author=None,
                        content="Receipt for donated cash emailed on {}.".format(date.today().isoformat())
                    )
            except RuntimeWarning as e:
                sale.send_receipt = False  # Don't want to try again until failure is addressed.
                failure_msg = "Tried to email receipt on {} but failed because:\n{}."
                SaleNote.objects.create(sale=sale, author=None,
                    content=failure_msg.format(date.today().isoformat(), str(e))
                )

    @staticmethod
    def send_receivable_invoices():
        mv = ReceivableInvoiceMailView()
        for rinv in ReceivableInvoice.objects.filter(send_invoice=True).all():
            try:
                sent = mv.send(rinv)
                if sent:
                    rinv.send_invoice = False
                    rinv.save()
                    ReceivableInvoiceNote.objects.create(invoice=rinv, author=None,
                        content="Receivable invoice emailed on {}.".format(date.today().isoformat())
                    )
            except RuntimeWarning as e:
                failure_msg = "Tried to email invoice on {} but failed because:\n{}."
                ReceivableInvoiceNote.objects.create(invoice=rinv, author=None,
                    content=failure_msg.format(date.today().isoformat(), str(e))
                )

    def handle(self, *args, **options):
        self.send_physical_donation_receipts()
        self.send_monetary_donation_receipts()
        self.send_receivable_invoices()

