
# Standard
import datetime
import logging
from typing import List, Tuple

# Third Party
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from dateutil import relativedelta

# Local
from tasks.models import Task, Claim, Nag, Worker, Work
from members.models import Member

__author__ = 'adrian'

VC_EMAIL = "Volunteer Coordinator <volunteer@xerocraft.org>"
XIS_EMAIL = "Xerocraft Internal Systems <xis@xerocraft.org>"


class Command(BaseCommand):

    help = "If work MTD doesn't match figure last reported, send worker and email with updated info."

    @staticmethod
    def send_report(member, work_list, total_dur):

        total_hrs = total_dur.total_seconds()/3600.0
        next_month = datetime.date.today() + relativedelta.relativedelta(months=1)
        next_month = next_month.strftime("%B")

        text_content_template = get_template('tasks/email_wmtd_template.txt')
        html_content_template = get_template('tasks/email_wmtd_template.html')
        d = {
            'member': member,
            'work_list': [x for x in work_list if x.work_duration is not None],
            # TODO: Add an unfinished work section to the templates.
            'unfinished_work_list': [x for x in work_list if x.work_duration is None],
            'total_dur': total_dur,
            'total_hrs': total_hrs,
            'next_month': next_month,
        }
        subject = 'Work Trade Report for '+member.username+ ', ' + datetime.date.today().strftime('%a %b %d')
        from_email = VC_EMAIL
        bcc_email = XIS_EMAIL
        to = member.email
        text_content = text_content_template.render(d)
        html_content = html_content_template.render(d)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def handle(self, *args, **options):
        work_lists = {}

        logger = logging.getLogger("tasks")

        # Process this month's work entries, gathering them by member:
        today = datetime.date.today()
        start_of_month = datetime.datetime(today.year, today.month, 1)
        for work in Work.objects.filter(work_date__gte=start_of_month):  # type: Work
            member = work.claim.claiming_member
            if member not in work_lists: work_lists[member] = []
            work_lists[member] += [work]

        # Look for work lists with totals that have changed since last report:
        for member, work_list in work_lists.items():  # type: Tuple[Member, List[Work]]

            if not member.worker.should_report_work_mtd:
                logger.info("%s has reportable WMTD but is NOT set for updates.", member)
                continue

            if member.email == "": continue

            total_wmtd = datetime.timedelta(0)  # type: datetime.timedelta
            for work in work_list:  # type: Work
                if work.work_duration is not None:
                    total_wmtd += work.work_duration
            if total_wmtd != member.worker.last_work_mtd_reported:
                logger.info("Sent email to %s regarding WMTD = %s", member, total_wmtd)
                Command.send_report(member, work_list, total_wmtd)
                member.worker.last_work_mtd_reported = total_wmtd
                member.worker.save()

