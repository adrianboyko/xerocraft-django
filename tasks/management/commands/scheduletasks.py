__author__ = 'adrian'

from django.core.management.base import BaseCommand, CommandError
from tasks.models import RecurringTaskTemplate, Task
import datetime


class Command(BaseCommand):
    help = 'Creates new tasks from templates, reschedules tasks that have slipped, etc.'

    def add_arguments(self, parser):
        parser.add_argument('num_days', type=int)

    @staticmethod
    def add_new_tasks(num_days):
        for template in RecurringTaskTemplate.objects.filter(active=True):
            template.create_tasks(num_days)

    @staticmethod
    def reschedule_missed_dates():
        today = datetime.date.today()
        for template in RecurringTaskTemplate.objects.all():
            tasks = template.instances.filter(
                status=Task.STAT_ACTIVE,
                scheduled_date__isnull=False
            ).order_by('scheduled_date')

            if len(tasks) == 0: continue
            t0 = tasks[0]
            if t0.scheduled_date >= today: continue

            if t0.missed_date_action == Task.MDA_SLIDE_SELF_AND_LATER:
                slide_delta = today - t0.scheduled_date
                for task in tasks:
                    task.scheduled_date += slide_delta
                    task.save()

            if t0.missed_date_action == Task.MDA_IGNORE:
                pass  # No action required

    def handle(self, *args, **options):
        Command.reschedule_missed_dates()
        Command.add_new_tasks(options['num_days'])

