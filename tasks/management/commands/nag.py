from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from tasks.models import Task, Claim, Nag, Worker
from members.models import Member
import datetime
from decimal import Decimal

__author__ = 'adrian'


def times():
    oneday = datetime.timedelta(days=1)
    threedays = datetime.timedelta(days=3)
    oneweek = datetime.timedelta(weeks=1)
    today = datetime.date.today()
    tomorrow = today + oneday
    todayplus3d = today + threedays
    todayplus1w = today + oneweek
    todayplus2w = today + oneweek + oneweek
    return oneday, today, tomorrow, todayplus3d, todayplus1w, todayplus2w


class Command(BaseCommand):

    help = "Emails members asking them to work tasks."

    @staticmethod
    def nag_for_workers():
        oneday, today, tomorrow, todayplus3d, todayplus1w, todayplus2w = times()

        # Find out who's doing what over the next 2 weeks. Who's already scheduled to work and who's heavily scheduled?
        ppl_already_scheduled = Claim.sum_in_period(today, todayplus2w)
        ppl_heavily_scheduled = set([member for member,dur in ppl_already_scheduled.items() if dur >= datetime.timedelta(hours=6.0)])

        # Rule out the following sets:
        ppl_excluded = set()
        ppl_excluded |= set([worker.member for worker in Worker.objects.filter(should_nag=False)])
        ppl_excluded |= set(Member.objects.filter(auth_user__email=""))
        ppl_excluded |= set(Member.objects.filter(auth_user__is_active=False))

        # Cycle through future days' NAGGING tasks to see which need workers and who should be nagged.
        nag_lists = {}
        for task in Task.objects.filter(scheduled_date__gte=today, scheduled_date__lt=todayplus3d, should_nag=True):

            # No need to nag if task is fully claimed or not workable.
            if (not task.status == Task.STAT_ACTIVE) or task.is_fully_claimed():
                continue

            potentials = task.all_eligible_claimants()
            potentials -= task.current_claimants()
            potentials -= set(task.uninterested.all())
            potentials -= ppl_excluded

            panic_situation = task.scheduled_date == today and task.priority == Task.PRIO_HIGH
            if not panic_situation:
                # Don't bother heavily scheduled people if it's not time to panic
                potentials -= ppl_heavily_scheduled

            for member in potentials:
                if member not in nag_lists:
                    nag_lists[member] = []
                nag_lists[member] += [task]

        # Send email messages:
        text_content_template = get_template('tasks/email_nag_template.txt')
        html_content_template = get_template('tasks/email_nag_template.html')
        for member, tasks in nag_lists.items():

            b64, md5 = Member.generate_auth_token_str(
                lambda token: Nag.objects.filter(auth_token_md5=token).count() == 0  # uniqueness test
            )

            nag = Nag.objects.create(who=member, auth_token_md5=md5)
            nag.tasks.add(*tasks)

            d = Context({
                'token': b64,
                'member': member,
                'tasks': tasks,
                #'host': 'http://192.168.1.101:8000'
                'host': 'http://xerocraft-django.herokuapp.com'
            })
            subject = 'Call for Volunteers, ' + datetime.date.today().strftime('%a %b %d')
            from_email = 'Volunteer Coordinator <volunteer@xerocraft.org>'
            to = member.email
            text_content = text_content_template.render(d)
            html_content = html_content_template.render(d)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

    @staticmethod
    def nag_for_keyholders():
        pass  #TODO

    def handle(self, *args, **options):

        self.nag_for_workers()
        self.nag_for_keyholders()
