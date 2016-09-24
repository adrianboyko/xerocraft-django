
# Standard

# Third Party
from django.core.management.base import BaseCommand

# Local
from members.models import Member
from tasks.models import Worker

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Creates a Worker instance for each Member that doesn't already have one."

    def handle(self, **options):
        for member in Member.objects.all():
            w,_ = Worker.objects.get_or_create(member=member)

