
# Standard
from datetime import date, timedelta
import json

# Third Party
from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User
from django.core import management, mail
from django.utils import timezone

# Local
from .models import Tag, Tagging, VisitEvent, Membership
from .views import _calculate_accrued_membership_revenue


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TestMemberNag(TestCase):

    def setUp(self):

        u = User.objects.create(
            username='fake1',
            first_name="Andrew", last_name="Baker",
            password="fake1",
            email="fake@example.com",
        )
        self.memb = u.member

        visit = VisitEvent.objects.create(
            who=self.memb,
            when=timezone.now() - timedelta(days=1),  # membernag looks at previous day's visits.
            method=VisitEvent.METHOD_RFID,
            event_type=VisitEvent.EVT_ARRIVAL
        )

    def test_paid_visit(self):

        # Create an CURRENT membership
        mship = Membership.objects.create(
            member=self.memb,
            membership_type=Membership.MT_COMPLIMENTARY,
            start_date=date.today()-timedelta(days=1),
            end_date=date.today()+timedelta(days=1),
        )
        mship.clean()
        mship.dbcheck()
        management.call_command("membernag")
        self.assertEqual(len(mail.outbox), 0)

    def test_unpaid_visit(self):

        # Create an OLD, EXPIRED membership
        mship = Membership.objects.create(
            member=self.memb,
            membership_type=Membership.MT_COMPLIMENTARY,
            # membernag gives member 14 days to pay, so make old membership older than that:
            start_date=date.today()-timedelta(days=21),
            end_date=date.today()-timedelta(days=20),
        )
        mship.clean()
        mship.dbcheck()
        management.call_command("membernag")
        self.assertEqual(len(mail.outbox), 1)

    def test_unpaid_visit_leeway(self):

        # Create an NOT-VERY-OLD, EXPIRED membership
        mship = Membership.objects.create(
            member=self.memb,
            membership_type=Membership.MT_COMPLIMENTARY,
            # membernag gives member 14 days to pay, so make old membership inside the leeway:
            start_date=date.today()-timedelta(days=11),
            end_date=date.today()-timedelta(days=10),
        )
        mship.clean()
        mship.dbcheck()
        management.call_command("membernag")
        self.assertEqual(len(mail.outbox), 0)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

"""
TODO: The following test is complicated by my signal processing.
Specifically, when loading a fixture there's no need for the handler that creates a member for each user.
"""
# class TestMemberValidity(TestCase):
#
#     fixtures = ['members.json']
#
#     @factory.django.mute_signals(signals.post_save)
#     def test_member_validity(self):
#         for u in User.objects.all():
#             m = u.member
#             self.assertTrue(m is not None)
#             valid,_ = m.validate()
#             self.assertTrue(valid)
#


class TestMembers(TestCase):

    def setUp(self):
        ab = User.objects.create(username='fake1', first_name="Andrew", last_name="Baker", password="fake1")

    #TODO: Remove this test if TestMemberValidity can be made to work.
    def test_member_validity(self):
        for u in User.objects.all():
            m = u.member
            self.assertTrue(m is not None)
            valid,_ = m.validate()
            self.assertTrue(valid)

    def test_member_auto_gen_content(self):
        for u in User.objects.all():
            m = u.member
            self.assertTrue(m is not None)
            tag_names = [x.name for x in m.tags.all()]
            self.assertTrue("Member" in tag_names) # Every member should have this tag.
            self.assertTrue(m.auth_user is not None) # Every member should be connected to a Django user.


class TestCardsAndApi(TestCase):

    def setUp(self):
        u1 = User.objects.create(username='fake1', first_name="Andrew", last_name="Baker", password="fake1")
        u2 = User.objects.create(username='fake2', first_name="Zhou", last_name="Yang", password="fake2")
        self.m1 = u1.member
        self.m2 = u2.member
        self.str1 = self.m1.generate_member_card_str()
        self.str2 = self.m2.generate_member_card_str()

    def test_member_details_non_staff(self):
        c = Client()
        path = "/members/api/member-details/%s_%s/" % (self.str1, self.str2)
        response = c.get(path)
        json_response = json.loads(response.content.decode())
        self.assertTrue(json_response['error'] == "Not a staff member")

    def test_member_details_is_staff(self):
        tag = Tag.objects.create(name="Staff", meaning="spam")
        tagging = Tagging.objects.create(tagged_member=self.m2, tag=tag, authorizing_member=self.m2)
        c = Client()
        path = "/members/api/member-details/%s_%s/" % (self.str1, self.str2)
        response = c.get(path)
        json_response = json.loads(response.content.decode())
        self.assertTrue(json_response['last_name'] == "Baker")

    def test_visit_event_good(self):
        c = Client()
        path = "/members/api/visit-event/%s_%s/" % (self.str1, VisitEvent.EVT_ARRIVAL)
        response = c.get(path)
        json_response = json.loads(response.content.decode())
        self.assertTrue(json_response['success'])

    def test_visit_event_bad_evt_type(self):
        c = Client()
        path = "/members/api/visit-event/%s_%s/" % (self.str1, 'BAD')
        response = c.get(path)
        self.assertTrue(response.status_code == 404)

    def test_visit_event_bad_member(self):
        c = Client()
        path = "/members/api/visit-event/%s_%s/" % (self.str1[:-1]+"X", 'A')
        response = c.get(path)
        json_response = json.loads(response.content.decode())
        self.assertTrue(json_response['error'])


class TestMembership(TestCase):

    def test_membership_ctrlid_generation(self):
        mship = Membership.objects.create(sale_price=0)
        self.assertTrue(mship.ctrlid.startswith("GEN"))


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# VIEWS

class TestViews(TestCase):

    def test_calculate_accrued_membership_revenue(self):
        _calculate_accrued_membership_revenue()
