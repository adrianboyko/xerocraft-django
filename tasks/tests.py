from django.test import TestCase
from tasks.models import Member, RecurringTaskTemplate

class TestMember(TestCase):

    def setUp(self):
        ab = Member.objects.create(first_name="Andrew", last_name="Baker", user_id="fake1")
        jr = Member.objects.create(first_name="Andrew Jr", last_name="Baker", user_id="fake2")
        jr.family_anchor = ab
        jr.save()
        ab.save()

    def test_member(self):
        ab = Member.objects.get(first_name="Andrew")
        self.assertEqual(ab.first_name, "Andrew")
        self.assertEqual(ab.last_name, "Baker")
        self.assertEqual(ab.user_id, "fake1")
        self.assertEqual(ab.family_anchor, None)
        jr = Member.objects.get(first_name="Andrew Jr")
        self.assertEqual(jr.family_anchor, ab)
        self.assertTrue(jr in ab.family_members.all())

class TestRecurringTask(TestCase):

    def setUp(self):
        rt1 = RecurringTaskTemplate.objects.create(short_desc="A test",work_estimate=1.5)

