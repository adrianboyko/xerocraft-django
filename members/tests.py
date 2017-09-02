
# Standard
from datetime import date, timedelta
import json
import os
import hashlib

# Third Party
from django.conf import settings
from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User
from django.core import management, mail
from django.utils import timezone
from django.core.urlresolvers import reverse
from freezegun import freeze_time
import members.notifications as notifications

# Local
from members.models import (
    Member, Tag, Tagging, VisitEvent, Membership, Pushover, MembershipGiftCard, DiscoveryMethod
)
from members.views import _calculate_accrued_membership_revenue
from members.notifications import pushover_available
from members.management.commands.membershipnudge import Command as MembershipNudgeCmd
import members.views as views


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TestMemberNag(TestCase):

    FREEZE_DATE_STR = "June 20, 2016, 10am"  # Date chosen to avoid open hacks.

    def setUp(self):

        with freeze_time(self.FREEZE_DATE_STR):

            u = User.objects.create_user(
                username='fake1',
                first_name="Andrew", last_name="Baker",
                password="fake1",
                email="fake@example.com",
            )
            self.memb = u.member  # type: Member
            self.memb.nag_re_membership = True
            self.memb.clean()
            self.memb.save()

            VisitEvent.objects.create(
                who=self.memb,
                when=timezone.now() - timedelta(days=1),  # membernag looks at previous day's visits.
                method=VisitEvent.METHOD_RFID,
                event_type=VisitEvent.EVT_ARRIVAL
            )

    def test_paid_visit(self):

        with freeze_time(self.FREEZE_DATE_STR):

            # Create an CURRENT membership
            mship = Membership.objects.create(
                member=self.memb,
                membership_type=Membership.MT_COMPLIMENTARY,
                start_date=date.today()-timedelta(days=1),
                end_date=date.today()+timedelta(days=1),
            )
            mship.clean()
            mship.dbcheck()
            management.call_command("membershipnudge", date=self.FREEZE_DATE_STR)
            self.assertEqual(len(mail.outbox), 0)

    def test_unpaid_visit(self):

        with freeze_time(self.FREEZE_DATE_STR):

            # Create an OLD, EXPIRED membership
            mship = Membership.objects.create(
                member=self.memb,
                membership_type=Membership.MT_COMPLIMENTARY,
                # Make old membership OLDER than membership nudge command's leeway:
                start_date=date.today()-MembershipNudgeCmd.leeway-timedelta(days=11),
                end_date=date.today()-MembershipNudgeCmd.leeway-timedelta(days=10),
            )
            mship.clean()
            mship.dbcheck()
            management.call_command("membershipnudge", date=self.FREEZE_DATE_STR)
            self.assertEqual(len(mail.outbox), 1)

    def test_unpaid_visit_leeway(self):

        with freeze_time(self.FREEZE_DATE_STR):

            # Create an NOT-VERY-OLD, EXPIRED membership
            mship = Membership.objects.create(
                member=self.memb,
                membership_type=Membership.MT_COMPLIMENTARY,
                # Make old membership exist INSIDE the leeway:
                start_date=date.today()-MembershipNudgeCmd.leeway+timedelta(days=2),
                end_date=date.today()-MembershipNudgeCmd.leeway+timedelta(days=3),
            )
            mship.clean()
            mship.dbcheck()
            management.call_command("membershipnudge", date=self.FREEZE_DATE_STR)
            self.assertEqual(len(mail.outbox), 0)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

"""
TODO: The following test is complicated by my signal handling.
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
        ab = User.objects.create_user(username='fake1', first_name="Andrew", last_name="Baker", password="fake1")

    # TODO: Remove this test if TestMemberValidity can be made to work.
    def test_member_validity(self):
        for u in User.objects.all():
            m = u.member
            self.assertTrue(m is not None)
            m.clean()

    def test_member_auto_gen_content(self):
        for u in User.objects.all():
            m = u.member
            self.assertTrue(m is not None)
            tag_names = [x.name for x in m.tags.all()]
            self.assertTrue("Member" in tag_names)  # Every member should have this tag.
            self.assertTrue(m.auth_user is not None)  # Every member should be connected to a Django user.


class TestCardsAndApi(TestCase):

    def setUp(self):
        u1 = User.objects.create_user(username='fake1', first_name="Andrew", last_name="Baker", password="fake1")
        u2 = User.objects.create_user(username='fake2', first_name="Zhou", last_name="Yang", password="fake2")
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
        Tagging.objects.create(tagged_member=self.m2, tag=tag, authorizing_member=self.m2)
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
        # This otherwise good test will fail because the test is run OUTSIDE the facility.
        self.assertTrue(json_response['error'].startswith("Must be on"))  # Must be on {} WiFi to check in/out

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


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# TEST REST APIs

class TestRestApi_Member(TestCase):

    def setUp(self):

        # Person who will make the REST API call
        caller = User.objects.create_user(
            username='caller',
            first_name="fn4caller", last_name="ln4caller",
            email="caller@example.com",
        )
        caller.set_password("pw4caller")
        try:
            caller.save()
        except Exception as x:
            print(x)
        caller.clean()
        caller.member.clean()
        self.caller = caller.member

        # The "Person of Interest" that the caller wants to learn about.
        poi = User.objects.create_user(
            username='poi',
            first_name="fn4poi", last_name="ln4poi",
            email="poi@example.com",
        )
        poi.set_password("pw4poi")
        poi.clean()
        poi.member.clean()
        self.poi = poi.member

        # The caller's "browser"
        self.client = Client()
        logged_in = self.client.login(username="caller", password="pw4caller")
        self.assertTrue(logged_in)

    def test_get_self(self):
        urlstr = reverse("memb:member-detail", kwargs={'pk': self.caller.auth_user.member.pk})
        response = self.client.get(urlstr)
        # Any member should be able to see their own private fields:
        self.assertContains(response, "caller@example.com")

    def test_get_other_as_regular(self):
        urlstr = reverse("memb:member-detail", kwargs={'pk': self.poi.auth_user.member.pk})
        response = self.client.get(urlstr)
        # Regular member should not be able to see private field of another member.
        self.assertNotContains(response, "poi@example.com")

    def test_get_as_director(self):
        tag = Tag.objects.create(name="Director", meaning="spam")
        Tagging.objects.create(tagged_member=self.caller, tag=tag)
        urlstr = reverse("memb:member-detail", kwargs={'pk': self.poi.auth_user.member.pk})
        response = self.client.get(urlstr)
        # Director should be able to see private field of another member.
        self.assertContains(response, "poi@example.com")

    def test_get_as_staff(self):
        tag = Tag.objects.create(name="Staff", meaning="spam")
        Tagging.objects.create(tagged_member=self.caller, tag=tag)
        urlstr = reverse("memb:member-detail", kwargs={'pk': self.poi.auth_user.member.pk})
        response = self.client.get(urlstr)
        # Staff should be able to see private field of another member.
        self.assertContains(response, "poi@example.com")


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# NOTIFY

class TestNotify(TestCase):

    def setUp(self):
        if pushover_available:
            self.user_key = os.getenv('XEROPS_PUSHOVER_USER_KEY', None)
            self.assertIsNotNone(self.user_key)
            self.user = User.objects.create_user(
                username='caller',
                first_name="John", last_name="Doe",
                email="jdoe@example.com",
            )
            Pushover.objects.create(
                who=self.user.member,
                key=self.user_key,
            )

    def test(self):
        if pushover_available:
            notifications.notify(self.user.member, "Testing Pushover", "This is a test.")


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# GENERATE GIFT CARDS

class GenGiftCards(TestCase):

    def test_dry_run(self):
        management.call_command('gengiftcards', 'TST', '50', '--months', '1', '--dry-run')
        self.assertEqual(MembershipGiftCard.objects.count(), 0)  # because it's a dry run

    def test_month_duration(self):
        management.call_command('gengiftcards', 'TST', '50', '--months', '1')
        self.assertEqual(MembershipGiftCard.objects.filter(month_duration=1).count(), 30)

    def test_day_duration(self):
        management.call_command('gengiftcards', 'TST', '50', '--days', '14')
        self.assertEqual(MembershipGiftCard.objects.filter(day_duration=14).count(), 30)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# RFID_ENTRY

class RfidEntry(TestCase):

    def setUp(self):
        self.unregistered_card = "12345678901234567890123456789012"
        self.registered_card = "987654321"
        self.memb = None
        self.client = Client()
        u = User.objects.create_user(
            username='fake1',
            first_name="Aaaa", last_name="Bbbb",
            password="fake1",
            email="fake@example.com",
        )
        self.memb = u.member  # type: Member
        self.memb.membership_card_md5 = hashlib.md5(self.registered_card.encode()).hexdigest()
        self.memb.clean()
        self.memb.save()

        # This simulates requests from inside the facility.
        views.FACILITY_PUBLIC_IP = "127.0.0.1"

    def tearDown(self):
        views.FACILITY_PUBLIC_IP = settings.XEROPS_FACILITY_PUBLIC_IP

    def test_ip(self):

        # The card number used for this test doesn't matter.
        # We're only testing handling of IP addresses.

        # This simulates a request from outside the facility.
        views.FACILITY_PUBLIC_IP = "1.1.1.1"
        path = reverse('memb:rfid-entry-granted', args=[self.registered_card])
        response = self.client.get(path)
        self.assertTrue(response.status_code == 403)  # Permission denied.

        # This simulates a request from inside the facility.
        views.FACILITY_PUBLIC_IP = "127.0.0.1"
        path = reverse('memb:rfid-entry-granted', args=[self.registered_card])
        response = self.client.get(path)
        self.assertTrue(response.status_code == 200)

    def test_unregistered_card(self):
        path = reverse('memb:rfid-entry-requested', args=[self.unregistered_card])
        response = self.client.get(path)
        self.assertTrue(response.status_code == 200)
        jr = json.loads(response.content.decode())
        self.assertFalse(jr['card_registered'])

    def test_registered_card_never_paid(self):
        path = reverse('memb:rfid-entry-requested', args=[self.registered_card])
        response = self.client.get(path)
        self.assertTrue(response.status_code == 200)
        jr = json.loads(response.content.decode())
        self.assertTrue(jr['card_registered'])
        self.assertFalse(jr['membership_current'])
        self.assertIsNone(jr['membership_start_date'])
        self.assertIsNone(jr['membership_end_date'])

    def test_registered_card_currently_paid(self):
        Membership.objects.create(
            member=self.memb,
            start_date=date.today()-timedelta(days=7),
            end_date=date.today()+timedelta(days=7),
        )
        path = reverse('memb:rfid-entry-requested', args=[self.registered_card])
        response = self.client.get(path)
        self.assertTrue(response.status_code == 200)
        jr = json.loads(response.content.decode())
        self.assertTrue(jr['card_registered'])
        self.assertTrue(jr['membership_current'])
        self.assertIsNotNone(jr['membership_start_date'])
        self.assertIsNotNone(jr['membership_end_date'])

    def test_registered_card_past_paid(self):
        Membership.objects.create(
            member=self.memb,
            start_date=date.today()-timedelta(days=14),
            end_date=date.today()-timedelta(days=7),
        )
        path = reverse('memb:rfid-entry-requested', args=[self.registered_card])
        response = self.client.get(path)
        self.assertTrue(response.status_code == 200)
        jr = json.loads(response.content.decode())
        self.assertTrue(jr['card_registered'])
        self.assertFalse(jr['membership_current'])
        self.assertIsNotNone(jr['membership_start_date'])
        self.assertIsNotNone(jr['membership_end_date'])

    def test_note_granted(self):
        path = reverse('memb:rfid-entry-granted', args=[self.registered_card])
        response = self.client.get(path)
        self.assertTrue(response.status_code == 200)

    def test_note_denied(self):
        path = reverse('memb:rfid-entry-denied', args=[self.registered_card])
        response = self.client.get(path)
        self.assertTrue(response.status_code == 200)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# RECEPTION KIOSK API

class TestReceptionKioskApi(TestCase):

    def setUp(self):
        self.pw = "fake"
        u = User.objects.create_user(
            username='abtest',
            first_name="Andrew", last_name="Baker",
            password=self.pw,
            email="fake@example.com",
        )
        self.memb = u.member  # type: Member
        self.memb.clean()

    def test_reception_kiosk_add_discovery_method(self):
        dm = DiscoveryMethod.objects.create(name="Spam", visible=True, order=1)
        urlstr = reverse("memb:reception-kiosk-add-discovery-method")
        data = {
            'member_pk': self.memb.pk,
            'member_pw': self.pw,
            'method_pk': dm.pk
        }
        response = self.client.post(urlstr, json.dumps(data), 'application/json')
        self.assertEqual(len(self.memb.discovery.all()), 1)

    def test_reception_kiosk_add_discovery_method_bad_pw(self):
        dm = DiscoveryMethod.objects.create(name="Spam", visible=True, order=1)
        urlstr = reverse("memb:reception-kiosk-add-discovery-method")
        data = {
            'member_pk': self.memb.pk,
            'member_pw': "WRONG",
            'method_pk': dm.pk
        }
        response = self.client.post(urlstr, json.dumps(data), 'application/json')
        self.assertEqual(response.status_code, 401)

    def test_reception_kiosk_set_is_adult(self):
        urlstr = reverse("memb:reception-kiosk-set-is-adult")
        data = {
            'member_pk': self.memb.pk,
            'member_pw': self.pw,
            'is_adult': True
        }
        response = self.client.post(urlstr, json.dumps(data), 'application/json')
        self.memb.refresh_from_db()
        self.assertIsNotNone(self.memb.is_adult)
        self.assertEqual(self.memb.is_adult, True)

    def test_reception_kiosk_set_is_adult_bad_pw(self):
        urlstr = reverse("memb:reception-kiosk-set-is-adult")
        data = {
            'member_pk': self.memb.pk,
            'member_pw': "WRONG",
            'is_adult': True
        }
        response = self.client.post(urlstr, json.dumps(data), 'application/json')
        self.assertEqual(response.status_code, 401)
