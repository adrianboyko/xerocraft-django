# Standard
from datetime import datetime
import logging

# Third Party
from django.core.management.base import BaseCommand
from django.utils import timezone

# Local
from members.models import Tag, Membership
from dateutil.relativedelta import relativedelta

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Creates complimentary memberships for directors"  # Comp will cover current month.
    logger = logging.getLogger("xerocraft-django")
    tz = timezone.get_default_timezone()

    def handle_member(self, member):

        start = datetime.replace(datetime.now(), day=1).date()
        end = start + relativedelta(months=1, days=-1)

        Membership.objects.create(
            member=member,
            protected=True,  # Otherwise it will attempt to reset member automatically
            membership_type=Membership.MT_COMPLIMENTARY,
            sale_price=0.0,
            start_date=start,
            end_date=end,
        )
        self.logger.info("Comp membership created for %s", str(member))

    def handle(self, *args, **options):

        for member in Tag.objects.get(name="Director").members.all():
            if member.is_currently_paid(): continue
            self.handle_member(member)

