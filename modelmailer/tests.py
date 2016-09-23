# Standard

# Third Party
from django.test import TestCase, TransactionTestCase
from django.core import mail

# Local
from books.mailviews import DonationMailView
from books.models import Donation
from modelmailer.mailviews import registrations


class DonationTests(TestCase):
    # TODO: These tests depend on the books app, which is bad. Replace with User (?) test views defined here.

    def test_normal(self):
        don = Donation.objects.create(donator_name="Frank", donator_email="frank@example.com")
        mv = DonationMailView()
        self.assertTrue(mv.send(don))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(registrations[Donation], DonationMailView)

    def test_bad_input(self):
        mv = DonationMailView()
        self.assertFalse(mv.send(None))

    def test_no_email_addr(self):
        don = Donation.objects.create(donator_name="Frank", donator_email="")
        mv = DonationMailView()
        self.assertFalse(mv.send(don))
