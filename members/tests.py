import json
from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User
from pydoc import locate  # for loading classes

#import factory
#from django.db.models import signals

from .models import Tag, Tagging, VisitEvent, Membership


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =]
# TODO: Generalize this so that it can be reused in multiple apps.
# TODO: Need a way to test Inlines. Maybe list Admin classes instead of model classes.

model_classnames = [
    # "MembershipInline",
    # "MembershipLineItem",
    "DiscoveryMethod",
    "MembershipGiftCardRedemption",
    "MembershipGiftCard",
    "MemberLogin",
    "Member",
    "Membership",
    "PaidMembership",
    "PaidMembershipNudge",
    "Tagging",
    "Tag",
    "VisitEvent",
]

admin_fieldname_lists = [
    'fields',
    'exclude',
    'readonly_fields',
    'list_display',
    'list_display_links',
    'search_fields',
    'filter_horizontal',
    'filter_vertical',
    'list_filter',
    'raw_id_fields',
]

admin_fieldname_singles = [
    'date_hierarchy',
]

class TestAdminConfig(TestCase):

    def test_admin_fieldname_lists(self):

        def check_fieldname(fieldname, model_class, admin_class):
            if not isinstance(fieldname, str): return
            fieldname = fieldname.replace("^", "")
            print("       field: %s" % fieldname)
            if fieldname in dir(model_class): return
            if fieldname in dir(admin_class): return
            model_class.objects.filter(**{fieldname:None})

        for model_classname in model_classnames:
            model_class = locate("members.models.%s" % model_classname)
            admin_class = locate("members.admin.%sAdmin" % model_classname)
            print("classes: %s, %s" % (model_class.__name__, admin_class.__name__))

            # Check lists of field names
            for list_name in admin_fieldname_lists:
                list_of_fieldnames = getattr(admin_class, list_name)
                if list_of_fieldnames is None: continue
                print("    list: %s" % list_name)
                for fieldname in list_of_fieldnames:
                    check_fieldname(fieldname, model_class, admin_class)

            # Check individual field names
            for single_name in admin_fieldname_singles:
                print("    single: %s" % single_name)
                fieldname = getattr(admin_class, single_name)
                check_fieldname(fieldname, model_class, admin_class)

            # Check fieldsets, which is a special case.
            fieldsets = getattr(admin_class, 'fieldsets')
            if fieldsets is not None:
                for fieldset_name, field_options in fieldsets:
                    print("    fieldset: %s" % fieldset_name)
                    fields = field_options["fields"]
                    for fieldname in fields:
                        check_fieldname(fieldname, model_class, admin_class)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =]


""" TODO: The following test is complicated by my signal processing.
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
