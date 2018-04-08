
# Standard
from datetime import datetime, timedelta, date
import logging
from typing import Set

# Third Party
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
import django.utils.timezone as timezone

# Local
from tasks.models import Worker, TimeAccountEntry
from tasks.views import render_time_acct_statement_as_html

__author__ = 'adrian'

VC_EMAIL = "Volunteer Coordinator <volunteer@xerocraft.org>"
XIS_EMAIL = "Xerocraft Internal Systems <xis@xerocraft.org>"


class Command(BaseCommand):

    help = "If any time account entries were recently added, send worker a new statement."

    @staticmethod
    def send_statement(user: User):
        subject = 'Work Trade Statement for '+user.username+ ', ' + date.today().strftime('%a %b %d')
        from_email = VC_EMAIL
        bcc_email = XIS_EMAIL
        to = user.email
        text_content = "Please view this message on a device that supports HTML email."
        html_content = render_time_acct_statement_as_html(user, "recent")
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def handle(self, *args, **options):
        logger = logging.getLogger("tasks")

        # Find all the latest time account entries:
        users_to_update = set()  # type: Set[User]
        _24_hrs_ago = timezone.now() - timedelta(hours=24)
        entries = TimeAccountEntry.objects.filter(when__gte=_24_hrs_ago)

        # From the recent entries, determine which users to update:
        for entry in entries:  # type: TimeAccountEntry
            worker = entry.worker  # type: Worker
            user = worker.member.auth_user  # type: User
            if not worker.should_report_work_mtd:
                logger.info("%s has time account activity but is not set for updates.", user.username)
                continue
            if user.email is None:
                logger.info("%s has time account activity but has no email address for statement.", user.username)
                continue
            users_to_update.add(user)

        # Send a statement to each of the users:
        for user in users_to_update:  # type: User
            logger.info("Sent latest work-trade statement to %s.", user.username)
            Command.send_statement(user)

