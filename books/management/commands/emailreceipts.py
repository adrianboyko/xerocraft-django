# Standard
from datetime import date

# Third party
from django.core.management.base import BaseCommand, CommandError

# Local
from books.models import Donation, DonationNote
from books.mailviews import DonationMailView

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Email receipts queued up during the day."

    def handle(self, *args, **options):
        mv = DonationMailView()
        for donation in Donation.objects.filter(send_receipt=True).all():
            sent = mv.send(donation)
            if sent:
                donation.send_receipt = False
                donation.save()
                DonationNote.objects.create(
                    donation=donation,
                    author=None,
                    content="Receipt emailed on {}.".format(date.today().isoformat())
                )