from django.test import TestCase
from books.models import MonetaryDonation


class TestMonetaryDonation(TestCase):

    def test_monetarydonation_ctrlid_generation(self):
        mdon = MonetaryDonation.objects.create(amount=100)
        self.assertTrue(mdon.ctrlid.startswith("GEN"))
