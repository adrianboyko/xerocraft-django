from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone
from books.models import Donation, DonationNote
from datetime import date
import logging

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Email receipts queued up during the day."
    logger = logging.getLogger("members")
    XIS_ADDR = "Xerocraft Systems <xis@xerocraft.org>"
    TREASURER_ADDR = "Xerocract Treasurer <treasurer@xerocraft.org>"

    def send_pysical_donation_receipt(self, donation: Donation):

        acct = donation.donator_acct

        text_content_template = get_template('books/email-phys-donation.txt')
        html_content_template = get_template('books/email-phys-donation.html')

        if donation.donator_email != "":
            donator_addr = donation.donator_email
        elif acct is not None and acct.email != "":
            donator_addr = acct.email
        else:
            self.logger.error("Physical donation #%d has no usable email address for receipt.", donation.pk)
            return False

        if acct is not None:
            first_name = acct.first_name
            if first_name == "": first_name = None
        else:
            first_name = None

        if donation.donator_name != "":
            full_name = donation.donator_name
        elif acct is not None:
            full_name = "{} {}".format(acct.first_name, acct.last_name).strip()
            if full_name == "": full_name = None
        else:
            full_name = None

        params = Context({
            'first_name': first_name,
            'full_name': full_name,
            'donation': donation,
            'items': donation.donateditem_set.all(),
        })

        msg = EmailMultiAlternatives(
            "Receipt for Donation to Xerocraft",   # Subject
            text_content_template.render(params),  # Text content
            self.XIS_ADDR,                         # From
            [donator_addr, self.TREASURER_ADDR],   # To
        )
        msg.attach_alternative(html_content_template.render(params), "text/html")
        msg.send()

        self.logger.info("Physical donation receipt sent to %s at %s", full_name, donator_addr)
        return True

    def handle(self, *args, **options):

        for donation in Donation.objects.filter(send_receipt=True).all():
            sent = self.send_pysical_donation_receipt(donation)
            if sent:
                donation.send_receipt = False
                donation.save()
                DonationNote.objects.create(
                    donation=donation,
                    author=None,
                    content="Receipt emailed on {}.".format(date.today().isoformat())
                )