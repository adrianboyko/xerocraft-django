from django.test import TestCase
from books.models import MonetaryDonation, Sale
from pydoc import locate  # for loading classes


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =]

class TestMonetaryDonation(TestCase):

    def test_monetarydonation_ctrlid_generation(self):
        sale = Sale.objects.create(total_paid_by_customer=100)
        mdon = MonetaryDonation.objects.create(sale=sale, amount=100)
        self.assertTrue(mdon.ctrlid.startswith("GEN"))


    def test_monetarydonation_checksum(self):
        sale = Sale.objects.create(total_paid_by_customer=100)
        mdon = MonetaryDonation.objects.create(sale=sale, amount=100)
        sum = sale.checksum()
        self.assertTrue(sum, 100)

