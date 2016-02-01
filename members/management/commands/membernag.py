from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone
from members.models import Member, PaidMembership, VisitEvent
from tasks.models import Work
from datetime import datetime, timedelta, time
from decimal import Decimal
import logging

__author__ = 'adrian'

# Why aren't these defined in datetime?
MONDAY    = 0
TUESDAY   = 1
WEDNESDAY = 2
THURSDAY  = 3
FRIDAY    = 4
SATURDAY  = 5
SUNDAY    = 6

# TODO: This command is Xerocraft specific. Move to "xerocraft"?

OPENHACKS = [
    (TUESDAY, time(18, 0, 0), time(22, 0, 0)),
    (THURSDAY, time(19, 0, 0), time(22, 0, 0)),
    (SATURDAY, time(12, 0, 0), time(16, 0, 0)),
]


class Command(BaseCommand):

    help = "Emails unpaid members who visit during paid member hours."
    logger = logging.getLogger("members")
    bad_visits = None
    most_recent_payment = None

    def note_bad_visit(self, visit, pm: PaidMembership):

        if visit.who in self.bad_visits:
            self.bad_visits[visit.who].append(visit)
        else:
            self.bad_visits[visit.who] = [visit]

        if visit.who not in self.most_recent_payment:
            self.most_recent_payment[visit.who] = pm

    def process_bad_visits(self):
        for member, pm in self.most_recent_payment.items():
            self.logger.info("%s %s (%s), last paid membership: %s to %s",
                member.first_name,
                member.last_name,
                member.username,
                pm.start_date if pm is not None else "-",
                pm.end_date if pm is not None else "-"
            )
            for visit in self.bad_visits[member]:
                when = timezone.localtime(visit.when)
                when = when.strftime("%a, %b %d, %I:%M %p")
                self.logger.info("visited: %s", when)

        '''
        # Send email messages:
        text_content_template = get_template('member/unpaid_visit_nag.txt')
        html_content_template = get_template('member/unpaid_visit_nag.html')

        for visit in []:

            subject = 'Your Xerocraft Membership'
            from_email = 'Volunteer Coordinator <volunteer@xerocraft.org>'
            to = member.email
            text_content = text_content_template.render(d)
            html_content = html_content_template.render(d)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        '''

    def nag_for_unpaid_visits(self):

        self.bad_visits = {}
        self.most_recent_payment = {}

        time_leeway = timedelta(hours=1)
        date_leeway = timedelta(days=14)

        today = timezone.make_aware(datetime.now(),timezone.get_default_timezone())
        yesterday = today - timedelta(days=1)

        yesterdays_visits = VisitEvent.objects.filter(when__range=[yesterday, today])
        for visit in yesterdays_visits:

            # Ignore the visit if it was during open hacks because all open hack visits are OK.
            for (hack_dow, hack_start, hack_end) in OPENHACKS:
                if visit.when.date().weekday() == hack_dow:
                    if hack_start-time_leeway <= visit.when.time() <= hack_end+time_leeway:
                        continue  # Because those are open hack hours

            # Ignore visits by directors (who have decided they don't need to pay)
            if visit.who.is_tagged_with("Director"): continue

            # Get most recent membership payment for visitor.
            try:
                pm = PaidMembership.objects.filter(member=visit.who).latest('start_date')
            except PaidMembership.DoesNotExist:
                # Don't nag people that have NEVER paid because either:
                #  1) It's too soon to bother the member.
                #  2) The member is hopeless and will never pay.
                continue

            if pm.start_date > yesterday.date():
                # Don't nag because there is a future paid membership.
                continue
            elif pm.start_date <= yesterday.date() <= pm.end_date:
                # Don't nag because the latest paid membership covers the visit.
                continue
            elif yesterday.date() <= pm.end_date+date_leeway:
                # Don't nag yet because we're giving the member some leeway to renew.
                continue
            else:
                # Nag this user.
                self.note_bad_visit(visit, pm)

        self.process_bad_visits()
        return

    def handle(self, *args, **options):

        self.nag_for_unpaid_visits()
        # There may be other sorts of nags here, in the future.
