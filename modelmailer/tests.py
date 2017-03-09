# Standard

# Third Party
from django.test import TestCase, TransactionTestCase
from django.core import mail

# Local
from books.mailviews import PhysicalDonationMailView
from books.models import Donation
from modelmailer.mailviews import MailView


class DonationTests(TestCase):
    # TODO: These tests depend on the books app, which is bad. Replace with User (?) test views defined here.

    def test_normal(self):
        don = Donation.objects.create(donator_name="Frank", donator_email="frank@example.com")
        mv = PhysicalDonationMailView()
        self.assertTrue(mv.send(don))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(MailView.for_model(Donation), PhysicalDonationMailView)

    def test_bad_input(self):
        mv = PhysicalDonationMailView()
        self.assertFalse(mv.send(None))

    def test_no_email_addr(self):
        don = Donation.objects.create(donator_name="Frank", donator_email="")
        mv = PhysicalDonationMailView()
        self.assertFalse(mv.send(don))
