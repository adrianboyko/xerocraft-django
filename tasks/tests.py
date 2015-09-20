from django.test import TestCase
from tasks.models import RecurringTaskTemplate, Task
from members.models import Tag
from django.contrib.auth.models import User
from datetime import date, timedelta


class TestRecurringTaskTemplateValidity(TestCase):

    def test_RecurringTaskTemplate_rules_against_db(self):
        for rtt in RecurringTaskTemplate.objects.all():
            valid,_ = rtt.validate()
            self.assertTrue(valid)


class TestTemplateToInstanceCopy(TestCase):

    def setUp(self):
        tag1 = Tag.objects.create(name="test1",meaning="foo")
        tag2 = Tag.objects.create(name="test2",meaning="bar")
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc = "A test",
            work_estimate = 1.5,
            start_date = date.today(),
            repeat_interval = 1,)

        self.rt.eligible_tags.add(tag1,tag2)
        self.rt.save()

    def test_field_copies(self):
        self.rt.create_tasks(max_days_in_advance=2)
        task = Task.objects.all()[:1].get()
        template = task.recurring_task_template

        #REVIEW: Is there a way to dynamically discover and test mixin fields instead of hard-coding them?

        self.assertEqual(task.owner, template.owner)
        self.assertEqual(task.instructions, template.instructions)
        self.assertEqual(task.short_desc, template.short_desc)
        self.assertEqual(task.max_claimants, template.max_claimants)
        self.assertEqual(task.reviewer, template.reviewer)
        self.assertEqual(task.work_estimate, template.work_estimate)
        self.assertTrue(len(task.eligible_tags.all())==2)
        self.assertEqual(set(task.uninterested.all()), set(template.uninterested.all()))
        self.assertEqual(set(task.eligible_claimants.all()), set(template.eligible_claimants.all()))
        self.assertEqual(set(task.eligible_tags.all()), set(template.eligible_tags.all()))


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
        self.rt.create_tasks(max_days_in_advance=27)
        self.assertEqual(len(Task.objects.all()),1)
        # create_tasks should be idempotent for a particular argument.
        self.rt.create_tasks(max_days_in_advance=27)
        self.assertEqual(len(Task.objects.all()),1)


class TestRecurringTaskTemplateIntervals(TestCase):

    def setUp(self):
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc = "A test",
            work_estimate = 1.5,
            start_date = date.today(),
            repeat_interval = 28)

    def test_create_tasks(self):
        self.rt.create_tasks(365)
        self.assertEqual(len(Task.objects.all()), 13)
        # create_tasks should be idempotent for a particular argument.
        self.rt.create_tasks(365)
        self.assertEqual(len(Task.objects.all()), 13)
