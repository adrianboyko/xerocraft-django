from django.core.management.base import NoArgsCommand
import unittest
from tasks.models import *

__author__ = 'adrian'


class Command(NoArgsCommand):

    help = "Runs validation against each object in the tasks app."

    def handle_noargs(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(DbCheck)
        unittest.TextTestRunner().run(suite)


class DbCheck(unittest.TestCase):

    def test_RecurringTaskTemplate_objs(self):
        for obj in RecurringTaskTemplate.objects.all():
            obj.full_clean()

    def test_Test_objs(self):
        for obj in Task.objects.all():
            obj.full_clean()

    def test_Claim_objs(self):
        for obj in Claim.objects.all():
            obj.full_clean()

    def test_Work_objs(self):
        for obj in Work.objects.all():
            obj.full_clean()

    def test_Nag_objs(self):
        for obj in Nag.objects.all():
            obj.full_clean()

    def test_TaskNote_objs(self):
        for obj in TaskNote.objects.all():
            obj.full_clean()

    def test_CalendarSettings_objs(self):
        for obj in CalendarSettings.objects.all():
            obj.full_clean()

