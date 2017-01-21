
# Standard
from decimal import Decimal
from datetime import date

# Third Party
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.management import call_command

# Local
from books.models import (
    MonetaryDonation, Sale,
    JournalEntry, JournalEntryLineItem,
    Account
)


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


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =]

class TestJournalEntries(TestCase):

    def setUp(self):

        self.expenses = Account.objects.create(
            name="Expenses",
            category=Account.CAT_EXPENSE,
            type=Account.TYPE_DEBIT,
            description="Expenses"
        )

        self.cash = Account.objects.create(
            name="Cash",
            category=Account.CAT_ASSET,
            type=Account.TYPE_DEBIT,
            description="Cash"
        )

        self.je = JournalEntry.objects.create(
            source_url="http://127.0.0.1/",
            when=date.today()
        )

    def test_good_transaction(self):

        jel1 = JournalEntryLineItem.objects.create(
            journal_entry=self.je,
            amount=Decimal(1.00),
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            account=self.expenses
        )
        jel1.full_clean()

        jel2 = JournalEntryLineItem.objects.create(
            journal_entry=self.je,
            amount=Decimal(1.00),
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            account=self.expenses
        )
        jel2.full_clean()

        jel3 = JournalEntryLineItem.objects.create(
            journal_entry=self.je,
            amount=Decimal(1.00),
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            account=self.expenses
        )
        jel3.full_clean()

        jel4 = JournalEntryLineItem.objects.create(
            journal_entry=self.je,
            amount=Decimal(3.00),
            action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
            account=self.cash
        )
        jel4.full_clean()

        self.je.full_clean()
        self.je.dbcheck()

    def test_bad_transaction(self):

        jel1 = JournalEntryLineItem.objects.create(
            journal_entry=self.je,
            amount=Decimal(1.00),
            action=JournalEntryLineItem.ACTION_BALANCE_INCREASE,
            account=self.expenses
        )
        jel1.full_clean()

        jel2 = JournalEntryLineItem.objects.create(
            journal_entry=self.je,
            amount=Decimal(3.00),
            action=JournalEntryLineItem.ACTION_BALANCE_DECREASE,
            account=self.cash
        )
        jel2.full_clean()

        self.je.full_clean()
        self.assertRaises(ValidationError, self.je.dbcheck)

    def test_generate(self):
        # TODO: generatejournal should have a test mode that raises exceptions?
        call_command("generatejournal")
