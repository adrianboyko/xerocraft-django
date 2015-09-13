__author__ = 'adrian'

from django.core.management.base import BaseCommand, CommandError
from tasks.models import RecurringTaskTemplate


class Command(BaseCommand):
    help = 'Creates new tasks from templates, reschedules tasks that have slipped, etc.'

    def add_arguments(self, parser):
        parser.add_argument('num_days', type=int)

    def handle(self, *args, **options):
        num_days = options['num_days']
        for template in RecurringTaskTemplate.objects.filter(active=True):
            template.create_tasks(num_days)

        #TODO: Reschedule sliding tasks

