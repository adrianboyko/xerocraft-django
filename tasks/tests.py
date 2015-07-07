from django.test import TestCase
from tasks.models import Member, RecurringTaskTemplate, Task
from django.contrib.auth.models import User
from datetime import date, timedelta

class TestMembers(TestCase):

    def setUp(self):
        ab = User.objects.create(username='fake1', first_name="Andrew", last_name="Baker", password="fake1")
        ab.save()

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