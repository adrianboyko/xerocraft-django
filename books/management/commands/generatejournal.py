# Standard

# Third party
from django.core.management.base import BaseCommand

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
        print("Deleting...")
        JournalEntry.objects.filter(frozen=False).delete()
        print("Generating...")
        for journaler_class in registered_journaler_classes:
            for journaler in journaler_class.objects.all():  # type: Journaler
                je = journaler.journal_entry
                if je is not None and je.frozen:
                    continue
                journaler.create_journalentry()
                #journaler.journal_entry.dbcheck()
        print("Done.")
