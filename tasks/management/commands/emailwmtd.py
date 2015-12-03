from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from tasks.models import Task, Claim, Nag, Worker, Work
from dateutil import relativedelta
import datetime
import logging

__author__ = 'adrian'


class Command(BaseCommand):

    help = "If work MTD doesn't match figure last reported, send worker and email with updated info."

    @staticmethod
    def send_report(member, work_list, total_dur):

        total_hrs = total_dur.total_seconds()/3600.0
        next_month = datetime.date.today() + relativedelta.relativedelta(months=1)
        next_month = next_month.strftime("%B")

        text_content_template = get_template('tasks/email_wmtd_template.txt')
        html_content_template = get_template('tasks/email_wmtd_template.html')
        d = Context({
            'member': member,
            'work_list': work_list,
            'total_dur': total_dur,
            'total_hrs': total_hrs,
            'next_month': next_month,
        })
        subject = 'Work Trade Report, ' + datetime.date.today().strftime('%a %b %d')
        from_email = 'Volunteer Coordinator <volunteer@xerocraft.org>'
        to = member.email
        text_content = text_content_template.render(d)
        html_content = html_content_template.render(d)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def handle(self, *args, **options):
        work_lists = {}

        logger = logging.getLogger("tasks")

        # Process this month's work entries, gathering them by member:
        today = datetime.date.today()
        start_of_month = datetime.datetime(today.year, today.month, 1)
        for work in Work.objects.filter(work_date__gte=start_of_month):
            member = work.claim.claiming_member
            if member not in work_lists: work_lists[member] = []
            work_lists[member] += [work]

        # Look for work lists with totals that have changed since last report:
        for member, work_list in work_lists.items():

            if not member.worker.should_report_work_mtd: continue
            if member.email == "": continue

            total_wmtd = datetime.timedelta(0)
            for work in work_list:
                total_wmtd += work.work_duration
            if total_wmtd != member.worker.last_work_mtd_reported:
                logger.info("Sent email to %s regarding WMTD = %s", member, total_wmtd)
                Command.send_report(member, work_list, total_wmtd)
                member.worker.last_work_mtd_reported = total_wmtd
                member.worker.save()

