# Standard
import sys
from decimal import Decimal

# Third party
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

# Local
from books.models import (
    JournalEntry, JournalEntryLineItem,
    Journaler, JournalLiner,
    registered_journaler_classes,
)

__author__ = 'adrian'


class Command(BaseCommand):

    help = "(Re)generates the journal from existing transactions."

    def process_journalliners(journaler: Journaler):
        related_objects = [
            f for f in journaler._meta.get_fields()
              if (f.one_to_many or f.one_to_one)
              and f.auto_created
              and not f.concrete
        ]
        link_names = [rel.get_accessor_name() for rel in related_objects]
        for link_name in link_names:
            children = getattr(journaler, link_name).all()
            for child in children:
                # The children include Notes and other objs of no interest here.
                if isinstance(child, JournalLiner):
                    child.create_journalentry_lineitems(journaler)

    def handle(self, *args, **options):
        print("Deleting unfrozen journal entries... ", end="")
        sys.stdout.flush()
        JournalEntry.objects.filter(frozen=False).delete()
        print("Done.")
        for journaler_class in registered_journaler_classes:
            # print("\rGenerating entries for {} transactions...".format(journaler_class.__name__))
            count = 0  # type: int
            total_count = journaler_class.objects.count()
            for journaler in journaler_class.objects.all():  # type: Journaler
                count += 1
                progress = 1.0 * count / total_count
                print("\r{:.0%} of {}s... ".format(progress, journaler_class.__name__), end="")
                oldje = journaler.journal_entry
                if oldje is None or not oldje.frozen:
                    journaler.create_journalentry()
            print("Done.")

        grand_total_debits = Decimal(0.0)
        grand_total_credits = Decimal(0.0)
        print("\nVerifying that individual journal entries balance...")
        for je in JournalEntry.objects.all():  # type: JournalEntry
            debits, credits = je.debits_and_credits()
            grand_total_debits += debits
            grand_total_credits += credits
            if debits != credits:
                print("\nJournal Entry #{} doesn't balance.".format(je.pk))
                print("   http://localhost:8000{}".format(je.source_url))  # TODO: Get base from sites app?
                for li in je.journalentrylineitem_set.all():
                    print("   {}".format(str(li)))
        print("\nDone.")
        print("")
        print("Grand total credits: {}", grand_total_credits)
        print(" Grand total debits: {}", grand_total_debits)
        print("         Difference: {}", grand_total_credits - grand_total_debits)
