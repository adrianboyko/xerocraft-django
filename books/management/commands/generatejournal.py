# Standard
from decimal import Decimal

# Third party
from django.core.management.base import BaseCommand

# Local
from books.models import (
    JournalEntry,
    Journaler, JournalLiner,
    registered_journaler_classes,
)

__author__ = 'adrian'


class Command(BaseCommand):

    help = "(Re)generates the journal from existing transactions."

    def handle(self, *args, **options):

        print("\nDeleting unfrozen journal entries... ", end="", flush=True)
        JournalEntry.objects.all().delete()
        print("Done.\n")

        for journaler_class in registered_journaler_classes:
            # print("\rGenerating entries for {} transactions...".format(journaler_class.__name__))
            count = 0  # type: int
            total_count = journaler_class.objects.count()
            for journaler in journaler_class.objects.all():  # type: Journaler
                count += 1
                progress = 1.0 * count / total_count
                print("\r{:.0%} of {}s... ".format(progress, journaler_class.__name__), end="")
                journaler.create_journalentry()
            print("Done.")

        print("\nSaving batches... ", end="", flush=True)
        Journaler.save_batch()
        JournalLiner.save_batch()
        print("Done.")

        grand_total_debits = Decimal(0.0)
        grand_total_credits = Decimal(0.0)
        err_count = 0
        print("\nVerifying that individual journal entries balance...")
        for je in JournalEntry.objects.all().prefetch_related("journalentrylineitem_set"):  # type: JournalEntry
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
