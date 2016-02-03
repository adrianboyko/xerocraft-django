from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone
from members.models import Member, Tag, Tagging, PaidMembership
from tasks.models import Work
from datetime import datetime, timedelta, time
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import logging

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Creates complimentary memberships for directors"  # Comp will cover current month.
    logger = logging.getLogger("xerocraft-django")
    tz = timezone.get_default_timezone()

    def handle(self, *args, **options):
        for member in Tag.objects.get(name="Director").members.all():
            if member.is_currently_paid(): continue
            start = datetime.now().date()
            end = start + relativedelta(months=1, days=-1)
            PaidMembership.objects.create(
                member=member,
                protected=True,  # Otherwise it will attempt to reset member automatically
                membership_type=PaidMembership.MT_COMPLIMENTARY,
                family_count=0,
                start_date=start,
                end_date=end,
                payer_name="",
                payer_email="",
                payer_notes="",
                payment_method=PaidMembership.PAID_BY_NA,
                paid_by_member=0,
                processing_fee=0,
                payment_date=start,
                # Don't specify ctrlid because we're not an ETL Fetcher.
            )
            self.logger.info("Comp membership created for %s", str(member))

