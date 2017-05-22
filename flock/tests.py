
# Standard
from datetime import datetime, date, timedelta
from decimal import Decimal

# Third-party
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from freezegun import freeze_time
import pytz
import pyinter as inter

# Local
from .models import (
    Person, Resource, GroupAvailability,
    ClassTemplate, PersonInClassTemplate, ResourceInClassTemplate,
    ScheduledClass, PersonInScheduledClass, ResourceInScheduledClass,
    TimePattern,
    LONG_AGO,
    TimeStamp, dt2ts,
)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def make_person(prefix:str) -> Person:
    user = User.objects.create(username=prefix, first_name=prefix+"FN", last_name=prefix+"LN")  # type:User
    person = Person.objects.create(django_user=user)  # type:Person
    person.full_clean()
    return person


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def make_class_template() -> ClassTemplate:

    template = ClassTemplate.objects.create(
        name="default",
        short_description="default",
        long_description="default",
        min_students_required=4,
        max_students_allowed=9,
        max_students_for_teacher=4,
        additional_students_per_ta=4,
        duration=Decimal("2.0"),
    )  # type: ClassTemplate
    template.full_clean()

    teacher = make_person("teach")  # type:Person
    assistant1 = make_person("assist1")  # type:Person
    assistant2 = make_person("assist2")  # type:Person
    student1 = make_person("student1")  # type: Person
    student2 = make_person("student2")  # type: Person

    pict1 = PersonInClassTemplate.objects.create(person=teacher, class_template=template, role=PersonInClassTemplate.ROLE_TEACHER)
    pict2 = PersonInClassTemplate.objects.create(person=assistant1, class_template=template, role=PersonInClassTemplate.ROLE_ASSISTANT)
    pict3 = PersonInClassTemplate.objects.create(person=assistant2, class_template=template, role=PersonInClassTemplate.ROLE_ASSISTANT)
    pict4 = PersonInClassTemplate.objects.create(person=student1, class_template=template, role=PersonInClassTemplate.ROLE_STUDENT)
    pict5 = PersonInClassTemplate.objects.create(person=student2, class_template=template, role=PersonInClassTemplate.ROLE_STUDENT)
    pict1.full_clean()
    pict2.full_clean()
    pict3.full_clean()
    pict4.full_clean()
    pict5.full_clean()

    return template


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def instantiate_class(ct: ClassTemplate, dt: datetime) -> ScheduledClass:
    assert dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None  # I.e. dt is not naive
    eicts = []
    for pict in ct.personinclasstemplate_set.all():
        eicts.append(pict)
    for rict in ct.resourceinclasstemplate_set.all():
        eicts.append(rict)
    begin_ts = dt2ts(dt)
    ival = inter.closed(begin_ts, begin_ts+3600)
    ga = GroupAvailability(eicts, ival)
    return ct.instantiate(ga)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class TestStudentCounts(TestCase):

    def test_student_seats_total(self) -> None:
        class_template = make_class_template()  # type: ClassTemplate
        scheduled_class = instantiate_class(class_template, timezone.now())  # type: ScheduledClass

        self.assertEqual(scheduled_class.student_seats_total, 0)

        for pisc in scheduled_class.personinscheduledclass_set.all():
            pisc.status = PersonInScheduledClass.STATUS_APPROVED
            pisc.save()

        self.assertEqual(scheduled_class.student_seats_total, 9)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class TestTimePattern(TestCase):

    range_start = date(2017, 4, 1)
    range_finish = date(2017, 4, 28)

    @classmethod
    def setUpTestData(cls):
        cls.p = make_person("person")  # type:Person
        cls.tp = TimePattern.objects.create(
            person=cls.p,
            disposition=TimePattern.DISPOSITION_AVAILABLE,
            wom=TimePattern.WOM_EVERY,
            dow=TimePattern.DOW_TUE,
            hour=6, minute=00, morning=False,
            duration=4.0
        )  # type: TimePattern
        cls.tpx = TimePattern.objects.create(
            person=cls.p,
            disposition=TimePattern.DISPOSITION_UNAVAILABLE,
            wom=TimePattern.WOM_2ND,
            dow=TimePattern.DOW_TUE,
            hour=6, minute=00, morning=False,
            duration=4.0
        )  # type: TimePattern

    def setUp(self):
        self.old_tz = timezone.get_current_timezone()
        # The test(s) would behave differently in different time zones.
        # Therefor, we need to specify one so we get consistent, testable results.
        timezone.activate(pytz.timezone("America/Phoenix"))

    def tearDown(self):
        timezone.activate(self.old_tz)

    def test_interval_set(self):
        iset = self.tp.as_interval_set(self.range_start, self.range_finish)
        expected = inter.IntervalSet([
            inter.closed(1491354000, 1491368400),  # Wed, 05 Apr 2017 01:00:00 to 05:00:00 GMT
            inter.closed(1491958800, 1491973200),  # Wed, 12 Apr 2017 01:00:00 to 05:00:00 GMT
            inter.closed(1492563600, 1492578000),  # Wed, 19 Apr 2017 01:00:00 to 05:00:00 GMT
            inter.closed(1493168400, 1493182800),  # Wed, 25 Apr 2017 01:00:00 to 05:00:00 GMT
        ])
        self.assertEqual(iset, expected)

    def test_persons_availability(self):
        avail = self.p.get_availability(self.range_start, self.range_finish)  # type: inter.IntervalSet
        expected = inter.IntervalSet([
            inter.closed(1491354000, 1491368400),  # Wed, 05 Apr 2017 01:00:00 to 05:00:00 GMT
            # inter.closed(1491958800, 1491973200),  # Wed, 12 Apr 2017 01:00:00 to 05:00:00 GMT Second Tuesday!
            inter.closed(1492563600, 1492578000),  # Wed, 19 Apr 2017 01:00:00 to 05:00:00 GMT
            inter.closed(1493168400, 1493182800),  # Wed, 25 Apr 2017 01:00:00 to 05:00:00 GMT
        ])
        self.assertEqual(avail, expected)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class TestClassTemplatePossibilities(TestCase):

    def test1(self):
        pit = pytz.utc.localize(datetime(2017, 2, 1))
        with freeze_time(pit):
            ct = make_class_template()
            ct.min_students_required = 2
            ct.save()
            for pict in ct.personinclasstemplate_set.all():
                TimePattern.objects.create(
                    person=pict.person,
                    disposition=TimePattern.DISPOSITION_AVAILABLE,
                    wom=TimePattern.WOM_EVERY,
                    dow=TimePattern.DOW_TUE,
                    hour=6, minute=00, morning=False,
                    duration=2.0
                )
            range_begin = date.today()
            range_end = range_begin + timedelta(days=30)
            solutions = ct.find_potential_solutions(range_begin, range_end)
            self.assertEqual(len(solutions), 4)

    def test2(self):
        pit = pytz.utc.localize(datetime(2017, 2, 1))
        with freeze_time(pit):
            ct = make_class_template()
            ct.min_students_required = 2
            ct.save()
            for pict in ct.personinclasstemplate_set.all():
                TimePattern.objects.create(
                    person=pict.person,
                    disposition=TimePattern.DISPOSITION_AVAILABLE,
                    wom=TimePattern.WOM_EVERY,
                    dow=TimePattern.DOW_TUE,
                    hour=6, minute=00, morning=False,
                    duration=1.0  # Interested people aren't available enough.
                )
            range_begin = date.today()
            range_end = range_begin + timedelta(days=30)
            solutions = ct.find_potential_solutions(range_begin, range_end)
            self.assertEqual(len(solutions), 0)

    def test3(self):
        pit = pytz.utc.localize(datetime(2017, 2, 1))
        with freeze_time(pit):
            ct = make_class_template()
            ct.min_students_required = 3  # Not enough interested students
            ct.save()
            for pict in ct.personinclasstemplate_set.all():
                TimePattern.objects.create(
                    person=pict.person,
                    disposition=TimePattern.DISPOSITION_AVAILABLE,
                    wom=TimePattern.WOM_EVERY,
                    dow=TimePattern.DOW_TUE,
                    hour=6, minute=00, morning=False,
                    duration=2.0
                )
            range_begin = date.today()
            range_end = range_begin + timedelta(days=30)
            solutions = ct.find_potential_solutions(range_begin, range_end)
            self.assertEqual(len(solutions), 0)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class Scenario001(TestCase):

    def test(self):

        # +-------------+
        # | January 1st |
        # +-------------+
        pit = pytz.utc.localize(datetime(2017, 1, 1))
        with freeze_time(pit):

            # Teacher joins service and provides their availability info.

            teach = make_person("teach")  # type:Person
            tp = TimePattern.objects.create(
                person=teach,
                disposition=TimePattern.DISPOSITION_AVAILABLE,
                wom=TimePattern.WOM_EVERY,
                dow=TimePattern.DOW_TUE,
                hour=6, minute=00, morning=False,
                duration=Decimal('3.0')
            )  # type: TimePattern
            tp.full_clean()
            tp = TimePattern.objects.create(
                person=teach,
                disposition=TimePattern.DISPOSITION_AVAILABLE,
                wom=TimePattern.WOM_EVERY,
                dow=TimePattern.DOW_THU,
                hour=6, minute=00, morning=False,
                duration=Decimal('4.0')
            )  # type: TimePattern
            tp.full_clean()

            # Student #1 joins service.
            stud1 = make_person("student1")  # type:Person

        # +--------------+
        # | January 10th |
        # +--------------+
        pit = pytz.utc.localize(datetime(2017, 1, 10))  # type: datetime
        with freeze_time(pit):

            # The teacher creates a class template requiring 2 students.

            ct = ClassTemplate.objects.create(
                name="Learn to X",
                short_description="Learn to X",
                long_description="Learn to X",
                min_students_required=2,
                max_students_allowed=4,
                max_students_for_teacher=4,
                additional_students_per_ta=1,
                duration=Decimal("2.0"),
            )  # type: ClassTemplate
            ct.full_clean()
            pict = PersonInClassTemplate.objects.create(
                person=teach,
                class_template=ct,
                role=PersonInClassTemplate.ROLE_TEACHER,
            )
            pict.full_clean()

            self.assertEqual(ct.interested_student_count, 0)
            solutions = ct.find_potential_solutions(pit.date(), pit.date() + timedelta(days=28))
            self.assertEqual(len(solutions), 0)

        # +--------------+
        # | January 11th |
        # +--------------+
        pit = pytz.utc.localize(datetime(2017, 1, 11))  # type: datetime
        with freeze_time(pit):

            # Student #1 expresses interest in the class.

            pict = PersonInClassTemplate.objects.create(
                person=stud1,
                class_template=ct,
                role=PersonInClassTemplate.ROLE_STUDENT,
            )
            pict.full_clean()

            self.assertEqual(ct.interested_student_count, 1)
            solutions = ct.find_potential_solutions(pit.date(), pit.date() + timedelta(days=28))
            self.assertEqual(len(solutions), 0)

        # +--------------+
        # | February 1st |
        # +--------------+
        pit = pytz.utc.localize(datetime(2017, 2, 1))  # type: datetime
        with freeze_time(pit):

            # Student #2 joins the service, provides their availability info, and expresses interest in the course.

            stud2 = make_person("student2")  # type:Person
            tp = TimePattern.objects.create(
                person=stud2,
                disposition=TimePattern.DISPOSITION_AVAILABLE,
                wom=TimePattern.WOM_3RD,
                dow=TimePattern.DOW_THU,
                hour=7, minute=00, morning=False,
                duration=3.0
            )  # type: TimePattern
            tp.full_clean()
            pict = PersonInClassTemplate.objects.create(
                person=stud2,
                class_template=ct,
                role=PersonInClassTemplate.ROLE_STUDENT,
            )  # type: PersonInClassTemplate
            pict.full_clean()

            self.assertEqual(ct.interested_student_count, 2)
            solutions = ct.find_potential_solutions(pit.date(), pit.date() + timedelta(days=28))
            actual = {x.timespan.lower_value for x in solutions}
            expected = {
                1487296800,  # 2/16/2017, 7:00 PM GMT-7:00
            }
            self.assertEqual(actual, expected)  # 2/16/2017, 7:00 PM GMT-7:00

        # +--------------+
        # | February 2nd |
        # +--------------+
        pit = pytz.utc.localize(datetime(2017, 2, 2))  # type: datetime
        with freeze_time(pit):

            # Student #3 joins the service, provides their availability info, and expresses interest in the course.

            stud3 = make_person("student3")  # type:Person
            tp = TimePattern.objects.create(
                person=stud3,
                disposition=TimePattern.DISPOSITION_AVAILABLE,
                wom=TimePattern.WOM_EVERY,
                dow=TimePattern.DOW_TUE,
                hour=7, minute=00, morning=False,
                duration=3.0
            )  # type: TimePattern
            tp.full_clean()
            pict = PersonInClassTemplate.objects.create(
                person=stud3,
                class_template=ct,
                role=PersonInClassTemplate.ROLE_STUDENT,
            )  # type: PersonInClassTemplate
            pict.full_clean()

            self.assertEqual(ct.interested_student_count, 3)
            solutions = ct.find_potential_solutions(pit.date(), pit.date() + timedelta(days=28))
            actual = {x.timespan.lower_value for x in solutions}
            expected = {
                1486519200,  # 02/07/2017, 7:00 PM GMT-7:00  (Tu)
                1487124000,  # 02/14/2017, 7:00 PM GMT-7:00  (Tu)
                1487296800,  # 02/16/2017, 7:00 PM GMT-7:00  (Thurs)
                1487728800,  # 02/21/2017, 7:00 PM GMT-7:00  (Tu)
                1488333600,  # 02/28/2017, 7:00 PM GMT-7:00  (Tu)
            }
            self.assertEqual(actual, expected)
