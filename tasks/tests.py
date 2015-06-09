from django.test import TestCase
from tasks.models import Member, RecurringTaskTemplate, Task
from datetime import date, timedelta

class TestMemberValidity(TestCase):

    def test_member_rules_against_db(self):
        for m in Member.objects.all():
            valid,_ = m.validate()
            self.assertTrue(valid)

class TestMemberWithFamily(TestCase):

    def setUp(self):
        ab = Member.objects.create(first_name="Andrew", last_name="Baker", user_id="fake1")
        jr = Member.objects.create(first_name="Andrew Jr", last_name="Baker", user_id="fake2")
        jr.family_anchor = ab
        jr.save()
        ab.save()

    def test_family(self):
        ab = Member.objects.get(first_name="Andrew")
        self.assertEqual(ab.first_name, "Andrew")
        self.assertEqual(ab.last_name, "Baker")
        self.assertEqual(ab.user_id, "fake1")
        self.assertEqual(ab.family_anchor, None)
        jr = Member.objects.get(first_name="Andrew Jr")
        self.assertEqual(jr.family_anchor, ab)
        self.assertTrue(jr in ab.family_members.all())

class TestRecurringTaskTemplateValidity(TestCase):
    def test_RecurringTaskTemplate_rules_against_db(self):
        for rtt in RecurringTaskTemplate.objects.all():
            valid,_ = rtt.validate()
            self.assertTrue(valid)

class TestRecurringTaskTemplateCertainDays(TestCase):

    def setUp(self):
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc = "A test",
            work_estimate = 1.5,
            start_date = date.today(),
            last = True,
            sunday = True)

    def test_greatest_scheduled_date(self):
        sched = self.rt.greatest_scheduled_date()
        start = self.rt.start_date
        self.assertTrue(type(sched) is date and type(start) is date)
        self.assertGreater(self.rt.start_date, sched)

    def test_create_tasks(self):
        self.rt.create_tasks(max_days_in_advance=28)
        self.assertEqual(len(Task.objects.all()),1)
        # create_tasks should be idempotent for a particular argument.
        self.rt.create_tasks(max_days_in_advance=28)
        self.assertEqual(len(Task.objects.all()),1)

class TestRecurringTaskTemplateIntervals(TestCase):

    def setUp(self):
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc = "A test",
            work_estimate = 1.5,
            start_date = date.today(),
            flexible_dates = True,
            repeat_interval = 28)

    def test_create_tasks(self):
        self.rt.create_tasks(60)
        self.assertEqual(len(Task.objects.all()),2)
        # create_tasks should be idempotent for a particular argument.
        self.rt.create_tasks(60)
        self.assertEqual(len(Task.objects.all()),2)