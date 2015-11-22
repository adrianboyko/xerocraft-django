
from django.core.management.base import NoArgsCommand
from members.models import Member
from tasks.models import Worker

__author__ = 'adrian'


class Command(NoArgsCommand):

    help = "Creates a Worker instance for each Member that doesn't already have one."

    def handle_noargs(self, **options):
        for member in Member.objects.all():
            w,_ = Worker.objects.get_or_create(member=member)

