# Standard
import sys
from decimal import Decimal

# Third party
from django.core.management.base import BaseCommand
from django.db.models import Max

# Local
from books.models import (
    JournalEntry, JournalEntryLineItem,
    Journaler, JournalLiner,
    registered_journaler_classes,
)

__author__ = 'adrian'


class Command(BaseCommand):

    help = "(Re)generates the journal from existing transactions."

    def handle(self, *args, **options):

        print("Deleting unfrozen journal entries... ", end="")
        sys.stdout.flush()
        JournalEntry.objects.filter(frozen=False).delete()
        print("Done.")
        Journaler._next_id = (JournalEntry.objects.all().aggregate(Max('id'))['id__max'] or 0) + 1

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

        JournalLiner.save_batch()  # Saves any incomplete batch that may have accumulated.

        grand_total_debits = Decimal(0.0)
        grand_total_credits = Decimal(0.0)
        err_count = 0
        print("\nVerifying that individual journal entries balance...")
        for je in JournalEntry.objects.all():  # type: JournalEntry
            debits, credits = je.debits_and_credits()
            grand_total_debits += debits
            grand_total_credits += credits
            if debits != credits:
                err_count += 1
                print("\nJournal Entry #{} doesn't balance.".format(je.pk))
                print("   http://localhost:8000{}".format(je.source_url))  # TODO: Get base from sites app?
                for li in je.journalentrylineitem_set.all():
                    print("   {}".format(str(li)))
        print("\nDone.\n")
        print("        Error count: {}".format(err_count))
        print("Grand total credits: {}".format(grand_total_credits))
        print(" Grand total debits: {}".format(grand_total_debits))
        print("         Difference: {}".format(grand_total_credits - grand_total_debits))
