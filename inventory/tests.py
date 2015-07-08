from django.test import TestCase, Client
from django.test.utils import override_settings
from django.utils import timezone
from tasks.models import Member
from inventory.models import ParkingPermit, PermitScan, Location
from django.contrib.auth.models import User
from datetime import date, timedelta


class TestStringReps(TestCase):

    def setUp(self):
        user = User.objects.create(username='fake1', first_name="Andrew", last_name="Baker", password="fake1")
        self.member = user.member
        permit = ParkingPermit.objects.create(owner=self.member, short_desc="Test")
        self.permit = permit;
        location = Location.objects.create()
        self.location = location
        scan = PermitScan.objects.create(permit=permit, where=location, when=timezone.now())
        self.scan = scan

    def test_strs(self):
        str(self.member)
        str(self.location)
        str(self.permit)
        str(self.scan)


