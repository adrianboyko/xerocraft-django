
# Standard
from datetime import date, timedelta
from decimal import Decimal

# Third-party
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

# Local
from .models import Person, PersonInMeeting, Meeting, Proposal


def default_meeting() -> Meeting:

    prop = Proposal.objects.create(
        min_students_required=4,
        max_students_allowed=8,
        max_students_for_teacher=4,
        additional_students_per_ta=4,
    )  # type: Proposal
    meet = Meeting.objects.create(
        proposal=prop,
        starts=timezone.now() - timedelta(days=7),
        duration=Decimal("2.0")
    )  # type: Meeting
    return meet


class TestGetMostRecentMeetingDate(TestCase):

    def test_no_meetings(self):

        u = User.objects.create(first_name="First", last_name="Last")
        p = Person.objects.create(django_user=u)  # type:Person
        d = p.most_recent_meeting_date  # type:date
        self.assertEqual(d, date.min)

    def test_one_meeting(self):

        meet = default_meeting()  # type: Meeting
        u = User.objects.create(first_name="First", last_name="Last")
        p = Person.objects.create(django_user=u)  # type:Person
        PersonInMeeting.objects.create(entity=p, meeting=meet, status=PersonInMeeting.STATUS_GOOD)
        d = p.most_recent_meeting_date  # type:date
        self.assertEqual(d, meet.starts)

    def test_rest_time(self):

        meet = default_meeting()  # type: Meeting
        u = User.objects.create(first_name="First", last_name="Last")
        p = Person.objects.create(django_user=u)  # type:Person
        PersonInMeeting.objects.create(entity=p, meeting=meet, status=PersonInMeeting.STATUS_GOOD)
        # default rest time is 1.
        self.assertFalse(p.is_resting)
        p.rest_time = 365
        p.save()
        self.assertTrue(p.is_resting)
