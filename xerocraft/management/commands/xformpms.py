from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth.models import User
from members.models import Membership, PaidMembership
from books.models import Sale, SaleNote
import logging

__author__ = 'adrian'


class Command(BaseCommand):

    logger = logging.getLogger("xerocraft-django")
    tz = timezone.get_default_timezone()
    adrian = User.objects.get(username='adrianb')

    def xform(self, pm):

        defaults = {
            "sale_date": pm.payment_date if pm.payment_date is not None else pm.start_date,
            "payer_name": pm.payer_name,
            "payer_email": pm.payer_email,
            "total_paid_by_customer": pm.paid_by_member,
            "processing_fee": pm.processing_fee,
            # TODO: Do we really need pm.payer_notes
        }

        ctrlid_prefix = "[tmp]"
        if pm.payment_method in [Sale.PAID_BY_CASH, Sale.PAID_BY_CHECK]:
            ctrlid_prefix = ""
        sale, created = Sale.objects.get_or_create(
            payment_method=pm.payment_method,
            ctrlid=ctrlid_prefix+pm.ctrlid,
            defaults=defaults
        )

        if created:
            if pm.payment_date is None:
                SaleNote.objects.create(
                    sale=sale,
                    content="Exact payment date was not recorded on spreadsheets from which this was transcribed.",
                    author=self.adrian
                )
            Membership.objects.create(
                sale=sale,
                member=pm.member,
                membership_type=pm.membership_type,
                start_date=pm.start_date,
                end_date=pm.end_date,
                protected=pm.protected,
                # Not correct, but it'll have to suffice for now.
                # The paid_by_member value is potentially off by the fee paid.
                # New version of ETL has correct value.
                sale_price=pm.paid_by_member,
            )

            for n in range(pm.family_count):
                Membership.objects.create(
                    sale=sale,
                    member=pm.member,  # A placeholder because we don't know who the member wants to assign this family membership to.
                    membership_type=Membership.MT_FAMILY,
                    start_date=pm.start_date,
                    end_date=pm.end_date,
                    protected=pm.protected,
                    sale_price=10.00,
                )

    def handle(self, *args, **options):

        xformable_methods = [
            PaidMembership.PAID_BY_WEPAY,
            PaidMembership.PAID_BY_2CO,
            PaidMembership.PAID_BY_SQUARE,
            PaidMembership.PAID_BY_CASH,
            PaidMembership.PAID_BY_CHECK,
        ]

        for pm in PaidMembership.objects.all():

            if pm.payment_method in xformable_methods:
                self.xform(pm)

            # TODO:
            # PaidMembership.PAID_BY_NA,
            # PaidMembership.PAID_BY_GIFT,
