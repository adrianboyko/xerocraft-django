# Standard
import datetime
import logging

# Third party
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.db.models import F
from django.conf import settings

# Local
from tasks.models import Task, Claim, Nag, Worker
from members.models import Member

__author__ = 'adrian'

EMAIL_XEROPS = settings.XEROPS_CONFIG['EMAIL_XEROPS']
EMAIL_VOLUNTEER = settings.XEROPS_CONFIG['EMAIL_VOLUNTEER']
EMAIL_ARCHIVE = settings.XEROPS_CONFIG['EMAIL_ARCHIVE']
EMAIL_STAFF_LIST = settings.XEROPS_CONFIG['EMAIL_STAFF_LIST']

ONEDAY = datetime.timedelta(days=1)
TWODAYS = ONEDAY + ONEDAY
THREEDAYS = TWODAYS + ONEDAY
FOURDAYS = THREEDAYS + ONEDAY
ONEWEEK = datetime.timedelta(weeks=1)
TWOWEEKS = ONEWEEK + ONEWEEK


class Command(BaseCommand):

    help = "Emails members asking them to work tasks."

    def add_arguments(self, parser):
        parser.add_argument('--host', default="https://xerocraft-django.herokuapp.com")

    @staticmethod
    def send_staffing_emergency_message(tasks, HOST):

        text_content_template = get_template('tasks/email-staffing-emergency.txt')
        html_content_template = get_template('tasks/email-staffing-emergency.html')

        d = {
            'tasks': tasks,
            'host': HOST,
            'vc': EMAIL_VOLUNTEER,
        }

        subject = 'Staffing Emergency! ' + datetime.date.today().strftime('%a %b %d')
        from_email = EMAIL_VOLUNTEER
        bcc_email = EMAIL_ARCHIVE
        to = EMAIL_VOLUNTEER  # Testing by sending to Volunteer. Will ultimately send to EMAIL_STAFF_LIST.
        text_content = text_content_template.render(d)
        html_content = html_content_template.render(d)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    @staticmethod
    def nag_for_workers(HOST):
        today = datetime.date.today()

        # Find out who's doing what over the next 2 weeks. Who's already scheduled to work and who's heavily scheduled?
        ppl_already_scheduled = Claim.sum_in_period(today, today+TWOWEEKS)
        ppl_heavily_scheduled = set([member for member, dur in ppl_already_scheduled.items() if dur >= datetime.timedelta(hours=6.0)])

        # Rule out the following sets:
        ppl_excluded = set()
        ppl_excluded |= set([worker.member for worker in Worker.objects.filter(should_nag=False)])
        ppl_excluded |= set(Member.objects.filter(auth_user__email=""))
        ppl_excluded |= set(Member.objects.filter(auth_user__is_active=False))

        # Cycle through future days' NAGGING tasks to see which need workers and who should be nagged.
        nag_lists = {}
        emergency_tasks = []
        for task in Task.objects.filter(scheduled_date__gte=today, scheduled_date__lt=today+THREEDAYS, should_nag=True):

            # No need to nag if task is fully claimed or not workable.
            if (not task.is_active()) or task.is_fully_claimed():
                continue

            potentials = task.all_eligible_claimants()
            potentials -= task.current_claimants()
            potentials -= task.uninterested_claimants()
            potentials -= ppl_excluded

            panic_situation = task.scheduled_date == today and task.priority == Task.PRIO_HIGH
            if panic_situation:
                emergency_tasks.append(task)
            else:
                # Don't bother heavily scheduled people if it's not time to panic
                potentials -= ppl_heavily_scheduled

            for member in potentials:
                if member not in nag_lists:
                    nag_lists[member] = []
                nag_lists[member] += [task]

        # Send staffing emergency message to staff list:
        if len(emergency_tasks) > 0:
            Command.send_staffing_emergency_message(emergency_tasks, HOST)

        # Send email nag messages to potential workers:
        text_content_template = get_template('tasks/email_nag_template.txt')
        html_content_template = get_template('tasks/email_nag_template.html')
        for member, tasks in nag_lists.items():

            b64, md5 = Member.generate_auth_token_str(
                lambda token: Nag.objects.filter(auth_token_md5=token).count() == 0  # uniqueness test
            )

            nag = Nag.objects.create(who=member, auth_token_md5=md5)
            nag.tasks.add(*tasks)

            d = {
                'token': b64,
                'member': member,
                'tasks': tasks,
                'host': HOST,
            }
            subject = 'Call for Volunteers, ' + datetime.date.today().strftime('%a %b %d')
            from_email = EMAIL_VOLUNTEER
            bcc_email = EMAIL_ARCHIVE
            to = member.email
            text_content = text_content_template.render(d)
            html_content = html_content_template.render(d)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

    @staticmethod
    def abandon_suspect_claims():
        """A default claim is 'suspect' if it's almost time to do the work but the claim is not verified."""

        logger = logging.getLogger("tasks")
        today = datetime.date.today()

        for claim in Claim.objects.filter(
          status = Claim.STAT_CURRENT,
          claimed_task__scheduled_date__range=[today+ONEDAY, today+TWODAYS],
          claiming_member=F('claimed_task__recurring_task_template__default_claimant'),
          date_verified__isnull=True):
            # If we get here, it means that we've asked default claimant to verify twice but haven't heard back.
            if claim.claiming_member not in claim.claimed_task.eligible_claimants.all():
                # It looks like person who set up the task forgot to make default claimant an eligible claimant.
                # So let's add the default claimant to the list of eligible claimants.
                claim.claimed_task.eligible_claimants.add(claim.claiming_member)
            # Change the default claimant's claim to (presumably) UNINTERESTED
            # because we now want to nag to ALL eligible claimants.
            claim.status = Claim.STAT_UNINTERESTED
            claim.save()

    @staticmethod
    def verify_default_claims(HOST):

        today = datetime.date.today()
        claims = Claim.objects.filter(
            status=Claim.STAT_CURRENT,
            claimed_task__scheduled_date__range=[today+THREEDAYS, today+FOURDAYS],
            # REVIEW: Is the following 'claiming_member' restriction actually required?
            claiming_member=F('claimed_task__recurring_task_template__default_claimant'),
            date_verified__isnull=True)

        if len(claims) == 0:
            # No default claims to process.
            return

        text_content_template = get_template('tasks/email-verify-claim.txt')
        html_content_template = get_template('tasks/email-verify-claim.html')

        for claim in claims:
            b64, md5 = Member.generate_auth_token_str(
                lambda token: Nag.objects.filter(auth_token_md5=token).count() == 0)  # uniqueness test

            nag = Nag.objects.create(who=claim.claiming_member, auth_token_md5=md5)
            nag.claims.add(claim)
            nag.tasks.add(claim.claimed_task)

            dow = claim.claimed_task.scheduled_weekday()

            d = {
                'claimant': claim.claiming_member,
                'claim': claim,
                'task': claim.claimed_task,
                'dow': dow,
                'auth_token': b64,
                'host': HOST,
            }

            # Send email messages:
            subject = 'Please verify your availability for this {}'.format(dow)
            from_email = EMAIL_VOLUNTEER
            bcc_email = EMAIL_ARCHIVE
            to = claim.claiming_member.email
            text_content = text_content_template.render(d)
            html_content = html_content_template.render(d)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

    def handle(self, *args, **options):

        HOST = options['host']

        # Order is significant!
        self.abandon_suspect_claims()
        self.verify_default_claims(HOST)
        self.nag_for_workers(HOST)
