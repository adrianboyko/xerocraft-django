# Standard
from datetime import date

# Third party
from django.core.management.base import BaseCommand, CommandError

# Local
from books.models import Donation, DonationNote, Sale, SaleNote
from books.mailviews import PhysicalDonationMailView, CashDonationMailView

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Email receipts queued up during the day."

    def handle(self, *args, **options):

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
