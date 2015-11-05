from django.core import management, mail
from django.core.urlresolvers import reverse
from django.test import TestCase, TransactionTestCase, Client, RequestFactory
from tasks.models import *
from tasks.views import *
from tasks.admin import *
from members.models import Member, Tag
from django.contrib.auth.models import User
from django.contrib.admin import site
from datetime import datetime, date, timedelta, time
from pydoc import locate  # for loading classes


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

model_classnames = [
    "RecurringTaskTemplate",
    "Task",
    "Nag",
    "Claim",
    "Work",
    "TaskNote",
    "CalendarSettings",
]

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


class TestTemplateToInstanceCopy(TransactionTestCase):

    def setUp(self):
        tag1 = Tag.objects.create(name="test1",meaning="foo")
        tag2 = Tag.objects.create(name="test2",meaning="bar")
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc = "A test",
            max_work = timedelta(hours=1.5),
            start_date = date.today(),
            repeat_interval = 1,
        )

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
        self.assertEqual(task.max_workers, template.max_workers)
        self.assertEqual(task.reviewer, template.reviewer)
        self.assertEqual(task.max_work, template.max_work)
        self.assertTrue(len(task.eligible_tags.all())==2)
        self.assertEqual(set(task.uninterested.all()), set(template.uninterested.all()))
        self.assertEqual(set(task.eligible_claimants.all()), set(template.eligible_claimants.all()))
        self.assertEqual(set(task.eligible_tags.all()), set(template.eligible_tags.all()))


class TestRecurringTaskTemplateCertainDays(TestCase):

    def setUp(self):
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc = "A test",
            max_work = timedelta(hours=1.5),
            start_date = date.today(),
            last = True,
            sunday = True,
        )

    def test_greatest_scheduled_date(self):
        sched = self.rt.greatest_scheduled_date()
        start = self.rt.start_date
        self.assertTrue(type(sched) is date and type(start) is date)
        self.assertGreater(self.rt.start_date, sched)

    def test_create_tasks(self):
        self.rt.create_tasks(max_days_in_advance=34)
        self.assertEqual(len(Task.objects.all()),1)
        # create_tasks should be idempotent for a particular argument.
        self.rt.create_tasks(max_days_in_advance=34)
        self.assertEqual(len(Task.objects.all()),1)


class TestRecurringTaskTemplateIntervals(TransactionTestCase):

    def setUp(self):
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc = "A test",
            max_work = timedelta(hours=1.5),
            start_date = date.today(),
            repeat_interval = 28)

    def test_create_tasks(self):
        self.rt.create_tasks(365)
        self.assertEqual(len(Task.objects.all()), 13)
        # create_tasks should be idempotent for a particular argument.
        self.rt.create_tasks(365)
        self.assertEqual(len(Task.objects.all()), 13)


class TestPriorityMatch(TestCase):

    def testPrioMatch(self):
        ''' There is admin code that depends on these being equal. '''
        self.assertEqual(Task.PRIO_LOW, RecurringTaskTemplate.PRIO_LOW)
        self.assertEqual(Task.PRIO_MED, RecurringTaskTemplate.PRIO_MED)
        self.assertEqual(Task.PRIO_HIGH, RecurringTaskTemplate.PRIO_HIGH)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =]

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
            model_class = locate("tasks.models.%s" % model_classname)
            admin_class = locate("tasks.admin.%sAdmin" % model_classname)
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


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TestViews(TestCase):

    def setUp(self):

        self.arbitrary_token_b64 = 'S2s8DNreTH2R92Dfhzcdhp1aGVV1X0wj'
        arbitrary_token_md5 = 'acd706cdada4cbaa339cae813a25c30f'
        self.user = User.objects.create_superuser(username='admin', password='123', email='')
        self.member = Member.objects.first()
        self.member.membership_card_md5 = arbitrary_token_md5
        self.member.save()
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc="Admin View Test",
            max_work=timedelta(hours=1.5),
            start_date=date.today(),
            repeat_interval=1)
        self.rt.eligible_claimants.add(self.member)
        self.rt.create_tasks(max_days_in_advance=3)
        self.task = Task.objects.first()
        TaskNote.objects.create(task=self.task, author=self.member, content="spam", status=TaskNote.INFO)
        self.nag = Nag.objects.create(who=self.member, auth_token_md5=arbitrary_token_md5)
        self.nag.tasks.add(self.task)
        self.claim= Claim.objects.create(
            claiming_member=self.member,
            claimed_task=self.task,
            claimed_duration=timedelta(hours=1.5))
        self.work = Work.objects.create(
            claim=self.claim,
            work_date=datetime.today(),
            work_duration=timedelta(hours=1.5))
        CalendarSettings.objects.create(who=self.member, token=arbitrary_token_md5)
        self.fact = RequestFactory()

    def test_admin_views(self):

        for model_classname in model_classnames:

            model_cls = locate("tasks.models.%s" % model_classname)
            admin_cls = locate("tasks.admin.%sAdmin" % model_classname)
            admin_inst = admin_cls(model_cls, site)
            model_inst = model_cls.objects.first()
            assert model_inst is not None, "Test didn't create instances of %s" % model_classname
            url = "/admin/tasks/%s/" % model_classname.lower()

            # Test the list view:
            request = self.fact.get(url)
            request.user = self.user
            response = admin_inst.changelist_view(request)
            self.assertEqual(response.status_code, 200, "Admin view failure: %s" % url)

            # Test the detail view:
            request = self.fact.get(url)
            request.user = self.user
            response = admin_inst.change_view(request, str(model_inst.pk))
            self.assertEqual(response.status_code, 200, "Admin view failure: %s" % url)

    def test_nag_offer_views(self):
        client = Client()

        url = reverse('task:offer-task', args=[str(self.task.pk), self.arbitrary_token_b64])
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

        # The claim and work were required for previous tests, but delete them because following will recreate them.
        self.work.delete()
        self.claim.delete()
        self.assertEqual(len(self.task.current_claimants()), 0)
        response = client.post(url, {'hours':"01:30:00"})
        # On success, response will redirect to next in the nag handling process.
        kwargs = {'task_pk':str(self.task.pk), 'auth_token':self.arbitrary_token_b64}
        self.assertRedirects(
            response,
            reverse('task:offer-more-tasks', kwargs=kwargs),
            302,  # POST to offer-task will respond with a redirect to offer-more-tasks
            302   # Because there are no other tasks on same day, offer-more-tasks will redirect to next in chain.
        )
        self.assertEqual(len(self.task.current_claimants()), 1)

        # Add more tasks so there is one on the same day of week and retry the previous.
        # This time it shouldn't redirect.
        Claim.objects.first().delete()  # Will be reclaiming the task again in this step.
        self.rt.create_tasks(max_days_in_advance=8)
        response = client.post(url, {'hours':"01:30:00"})
        self.assertRedirects(
            response,
            reverse('task:offer-more-tasks', kwargs=kwargs),
            302,  # POST to offer-task will respond with a redirect to offer-more-tasks
            200   # Because there ARE other tasks on same day, offer-more-tasks will not redirect.
        )
        self.assertTrue(self.task.is_fully_claimed())

        response = client.post(
            reverse('task:offer-more-tasks', kwargs=kwargs),
            {'tasks':[str(Task.objects.last().pk)]}
        )
        self.assertTrue(response.status_code, 200)
        self.assertEqual(len(Claim.objects.all()), 2)

    def test_kiosk_views(self):
        client = Client()

        t = Task.objects.create(short_desc="Test Kiosk Views", max_work=timedelta(hours=2), max_workers=1)
        t.eligible_claimants.add(self.member)

        # Must test this "members" app view because "tasks" is hooked into it and can cause it to fail.
        url = reverse('memb:kiosk-check-in-member', args=[self.arbitrary_token_b64, VisitEvent.EVT_ARRIVAL])
        response = client.get(url)
        self.assertContains(response, "Test Kiosk Views", status_code=200)

    def test_calendar_views(self):

        t = Task.objects.create(
            short_desc="TCV",
            max_work=timedelta(hours=2),
            max_workers=1,
            work_start_time=time(19,00,00),
            work_duration=timedelta(hours=2),
            scheduled_date=date.today(),
        )

        expected_words = ["TCV","BEGIN","SUMMARY","DTSTART","DTEND","DTSTAMP","UID","DESCRIPTION","URL","END"]

        client = Client()
        url = reverse('task:xerocraft-calendar')
        response = client.get(url)
        for word in expected_words:
            self.assertContains(response, word)

        url = reverse('task:xerocraft-calendar-unstaffed')
        response = client.get(url)
        for word in expected_words:
            self.assertContains(response, word)

        c = Claim.objects.create(
            claimed_task=t,
            claiming_member=self.member,
            claimed_duration=t.work_duration,
            claimed_start_time=t.work_start_time,
            status=Claim.STAT_CURRENT,
        )
        t.claim_set.add(c)

        url = reverse('task:xerocraft-calendar-staffed')
        response = client.get(url)
        for word in expected_words:
            self.assertContains(response, word)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class RunSchedAndNagCmds(TestCase):
    """It's best to run scheduletasks before nag, so this test does both."""

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='123', email='test@example.com')
        member = Member.objects.first()
        self.rt = RecurringTaskTemplate.objects.create(
            short_desc="Sched and Nag Cmd Test",
            max_work=timedelta(hours=1.5),
            max_workers=1,
            work_start_time=time(19, 0, 0),
            work_duration=timedelta(2),
            start_date=date.today(),
            repeat_interval=1,
            should_nag=True)
        self.rt.eligible_claimants.add(member)

    def test_run_nagger(self):
        management.call_command("scheduletasks", "2")
        management.call_command("nag")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(Nag.objects.all()), 1)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class RunDbCheckCmd(TestCase):

    def test_database_validity(self):
        management.call_command("dbchecktasks")
