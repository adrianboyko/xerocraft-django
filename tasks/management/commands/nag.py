__author__ = 'adrian'

from django.core.management.base import BaseCommand, CommandError
from tasks.models import Task
import datetime


class Command(BaseCommand):

    help = "Emails members asking them to work tasks."

    def handle(self, *args, **options):
        for task in Task.objects.filter(scheduled_date__gte=datetime.date.today()):
            pass