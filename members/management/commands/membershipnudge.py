
# Standard
from datetime import datetime, date, timedelta, time
import logging

# Third Party
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import timezone
from django.conf import settings
from freezegun import freeze_time

# Local
from members.models import Membership, VisitEvent

__author__ = 'adrian'

EMAIL_TREASURER = settings.XEROPS_CONFIG['EMAIL_TREASURER']
EMAIL_ARCHIVE = settings.XEROPS_CONFIG['EMAIL_ARCHIVE']

# Why aren't these defined in datetime?
MONDAY    = 0
TUESDAY   = 1
WEDNESDAY = 2
THURSDAY  = 3
FRIDAY    = 4
SATURDAY  = 5
SUNDAY    = 6


OPENHACKS = [
    (TUESDAY, time(18, 0, 0), time(22, 0, 0)),
    (THURSDAY, time(19, 0, 0), time(22, 0, 0)),
    (SATURDAY, time(12, 0, 0), time(16, 0, 0)),
]

logger = logging.getLogger("xerocraft-django")


# TODO: Combine this command with the login scraper so it sends email shortly after person arrives?
# TODO: Should send an alert to staff members' Xerocraft apps.
# TODO: Handle membership nudges via generic "object mailer" mechanism?
class Command(BaseCommand):

    help = "Emails unpaid members who visit during paid member hours."

    # This is the length of the "leeway" or "grace period" before which we'll nag.
    # I'm choosing a very conservative value here.
    leeway = timedelta(days=31)

    def __init__(self):
        super().__init__()
        self.tz = timezone.get_default_timezone()
        self.today = None
        self.yesterday = None

    def add_arguments(self, parser):
        # Intended for test cases which will run on a specific date.
        parser.add_argument('--date')

    def process_bad_visitors(self, bad_visitors):
        for member, (pm, visit) in bad_visitors.items():

            if member.email in [None, ""]:
                logger.info("Bad visit by %s but they haven't provided an email address.", member.username)
                continue

            # Send email messages:
            text_content_template = get_template('members/email-unpaid-visit.txt')
            html_content_template = get_template('members/email-unpaid-visit.html')

            d = {
                'friendly_name': member.friendly_name,
                'paid_membership': pm,
                'bad_visit': visit,
            }

            subject = 'Please Renew your Xerocraft Membership'
            from_email = EMAIL_TREASURER
            bcc_email = EMAIL_ARCHIVE
            to = EMAIL_ARCHIVE  # TODO: Switch this to the actual visitor's email when ready for production.
            text_content = text_content_template.render(d)
            html_content = html_content_template.render(d)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            logger.info("Email sent to %s re bad visit.", member.username)
            pm.when_nudged = date.today()
            pm.nudge_count += 1
            pm.save()

    # TODO: "Open" times should be defined in a database table.
    def during_open_hack(self, visit):
        assert timezone.localtime(visit.when).date() == self.yesterday.date()
        time_leeway = timedelta(hours=1)
        for (hack_dow, hack_start, hack_end) in OPENHACKS:
            visit_dow = timezone.localtime(visit.when).weekday()
            if visit_dow == hack_dow:
                hack_start = self.tz.localize(datetime.combine(self.yesterday, hack_start))
                hack_end = self.tz.localize(datetime.combine(self.yesterday, hack_end))
                if hack_start-time_leeway <= visit.when <= hack_end+time_leeway:
                    return True
        return False

    def collect_bad_visitors(self):

        # NOTE: Don't want "members" to depend on "tasks".
        # This attempts to dynamically load "tasks".
        # Later code will analyze task data IFF it loaded.
        try:
            tasks = __import__("tasks", fromlist=[''])
            Work = tasks.models.Work
        except ImportError:
            # The website doesn't have "tasks" installed.
            Work = None

        bad_visitors = {}

        yesterdays_visits = VisitEvent.objects.filter(when__range=[self.yesterday, self.today])
        for visit in yesterdays_visits:
            pms = None
            work_count = None

            if self.during_open_hack(visit):
                # Ignore the visit if it was during open hacks because all open hack visits are OK.
                continue

            if visit.who.is_tagged_with("Director"):
                # Ignore visits by directors (who have decided they don't need to pay).
                continue

            pms = Membership.objects.filter(member=visit.who).all()
            if len(pms) == 0:
                # Don't nag people that have NEVER paid because either:
                #  1) It's too soon to bother the member.
                #  2) The member is hopeless and will never pay.
                continue
            else:
                covered = False
                for pm in pms:
                    if pm.start_date <= visit.when.date() <= (pm.end_date + self.leeway):
                        # Don't nag because the latest paid membership covers the visit.
                        # Note that there's some leeway in this to allow time for payments to be processed.
                        covered = True
                        break
                    if pm.start_date > visit.when.date():
                        # Don't nag because there is a future paid membership.
                        covered = True
                        break
                if covered:
                    continue

            if Work is not None:
                work_count = Work.objects.filter(
                    claim__claiming_member=visit.who, work_date=visit.when.date()
                ).count()
                if work_count > 0:
                    # Don't nag somebody who did volunteer work the day they visited.
                    continue

            if pm.when_nudged == self.today.date():
                # Don't nag somebody more than once per day.
                continue

            # Make a note to nag this visitor
            if visit.who not in bad_visitors:
                bad_visitors[visit.who] = (pm, visit)

        return bad_visitors

    def handle(self, *args, **options):

        # The "date" option supports test cases that run on specific dates.
        test_time = options['date']
        if test_time is not None:
            freezer = freeze_time(test_time)
            freezer.start()

        self.today = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        self.today = timezone.make_aware(self.today, timezone.get_default_timezone())
        self.yesterday = self.today - timedelta(days=1)

        bad_visitors = self.collect_bad_visitors()
        self.process_bad_visitors(bad_visitors)

        if test_time is not None:
            freezer.stop()