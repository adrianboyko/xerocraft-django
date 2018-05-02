# Standard
from typing import List

# Third party
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.sites.models import Site

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
            print("{}s".format(journaler_class.__name__), flush=True)
            print("   Loading data ... ", end="", flush=True)
            links = journaler_class.link_names_of_relevant_children()
            journalers = journaler_class.objects.all().prefetch_related(*links)  # type: List[Journaler]
            for journaler in journalers:
                if count==0:
                    print("Done.", flush=True)
                count += 1
                progress = 1.0 * count / total_count
                print("\r   Processed {:.0%} ... ".format(progress), end="")
                journaler.create_journalentry()
            print("Done.\n")

        Journaler.save_batch()
        JournalLiner.save_batch()

        errors = journaler_class.get_unbalanced_journal_entries()
        print("Found {} Errors:".format(len(errors)))
        for je in errors:
            url = je.source_url
            if settings.DEBUG:
                url = url.replace(Site.objects.get_current().domain, "localhost:8000")
            print("\n   {} doesn't balance:".format(je))
            print("      "+url)
            for li in je.journalentrylineitem_set.all():
                print("      {}".format(str(li)))

        total_dr = journaler_class._grand_total_debits
        total_cr = journaler_class._grand_total_credits
        total_diff = total_cr - total_dr
        print("\nTotals")
        print("  debits:  {0:9.2f}".format(total_dr))
        print("  credits: {0:9.2f}".format(total_cr))
        print("  diff:    {0:9.2f}".format(total_diff))

        print("\nDone.\n")
