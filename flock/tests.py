
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
    ClassTemplate, ScheduledClass,
    Person, PersonInClassTemplate, PersonInScheduledClass,
    Resource, ResourceInClassTemplate, ResourceInScheduledClass,
    TimePattern,
    LONG_AGO,
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
class TestGetMostRecentMeetingDate(TestCase):

    def test_no_scheduled_classes(self) -> None:

        u = User.objects.create(first_name="First", last_name="Last")
        p = Person.objects.create(django_user=u)  # type:Person
        d = p.most_recent_class_start  # type:date
        self.assertEqual(d, LONG_AGO)

    def test_one_scheduled_class(self) -> None:

        class_template = make_class_template()  # type: ClassTemplate
        scheduled_class = class_template.instantiate(timezone.now()-timedelta(days=7))  # type: ScheduledClass
        scheduled_class.status = ScheduledClass.STATUS_VERIFIED
        scheduled_class.save()
        p = scheduled_class.personinscheduledclass_set.all()[0].person
        d = p.most_recent_class_start  # type:date
        self.assertEqual(d, scheduled_class.starts)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class TestRestTime(TestCase):

    def test_rest_time(self) -> None:
        DAYS_AGO = 7
        class_template = make_class_template()  # type: ClassTemplate
        scheduled_class = class_template.instantiate(timezone.now()-timedelta(days=DAYS_AGO))  # type: ScheduledClass
        scheduled_class.status = ScheduledClass.STATUS_VERIFIED
        scheduled_class.save()
        p = scheduled_class.personinscheduledclass_set.all()[0].person

        p.rest_time = DAYS_AGO/2.0
        p.save()
        self.assertFalse(p.is_resting)

        p.rest_time = 365
        p.save()
        self.assertTrue(p.is_resting)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class TestStudentCounts(TestCase):

    def test_student_seats_total(self) -> None:
        class_template = make_class_template()  # type: ClassTemplate
        scheduled_class = class_template.instantiate(timezone.now())  # type: ScheduledClass

        self.assertEqual(scheduled_class.student_seats_total, 0)

        for pisc in scheduled_class.personinscheduledclass_set.all():
            pisc.status = PersonInScheduledClass.STATUS_APPROVED
            pisc.save()

        self.assertEqual(scheduled_class.student_seats_total, 9)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class TestTimePattern(TestCase):

    def test_interval_set(self):
        timezone.activate(pytz.timezone("America/Phoenix"))
        p = make_person("person")  # type:Person
        tp = TimePattern.objects.create(
            person=p,
            disposition=TimePattern.DISPOSITION_AVAILABLE,
            wom=TimePattern.WOM_EVERY,
            dow=TimePattern.DOW_TUE,
            hour=6, minute=00, morning=False,
            duration=4.0
        )  # type: TimePattern
        iset = tp.as_interval_set(timezone.datetime(2017, 4, 1), timezone.datetime(2017, 4, 28))
        expected = inter.IntervalSet([
            inter.closed(1491354000, 1491368400),  # Wed, 05 Apr 2017 01:00:00 to 05:00:00 GMT
            inter.closed(1491958800, 1491973200),  # Wed, 12 Apr 2017 01:00:00 to 05:00:00 GMT
            inter.closed(1492563600, 1492578000),  # Wed, 19 Apr 2017 01:00:00 to 05:00:00 GMT
            inter.closed(1493168400, 1493182800),  # Wed, 25 Apr 2017 01:00:00 to 05:00:00 GMT
        ])
        self.assertEqual(iset, expected)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class Scenario001(TestCase):

    def test(self):

        # +-------------+
        # | January 1st |
        # +-------------+
        with freeze_time(pytz.utc.localize(datetime(2017, 1, 1))):

            # Teacher joins service and provides their availability info.

            teach = make_person("teach")  # type:Person
            tp1 = TimePattern.objects.create(
                person=teach,
                disposition=TimePattern.DISPOSITION_AVAILABLE,
                wom=TimePattern.WOM_EVERY,
                dow=TimePattern.DOW_TUE,
                hour=6, minute=00, morning=False,
                duration=4.0
            )  # type: TimePattern
            tp1.full_clean()
            tp2 = TimePattern.objects.create(
                person=teach,
                disposition=TimePattern.DISPOSITION_AVAILABLE,
                wom=TimePattern.WOM_EVERY,
                dow=TimePattern.DOW_THU,
                hour=6, minute=00, morning=False,
                duration=4.0
            )  # type: TimePattern
            tp2.full_clean()

            # Student #1 joins service but does NOT provide availability info.
            stud1 = make_person("student1")  # type:Person

        # +--------------+
        # | January 10th |
        # +--------------+
        with freeze_time(pytz.utc.localize(datetime(2017, 1, 10))):

            # The teacher creates a class template requiring 2 students.

            ct = ClassTemplate.objects.create(
                name="Learn to X",
                short_description="Learn to X",
                long_description="Learn to X",
                min_students_required=2,
                max_students_allowed=4,
                max_students_for_teacher=4,
                additional_students_per_ta=0,
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

        # +--------------+
        # | January 11th |
        # +--------------+
        with freeze_time(pytz.utc.localize(datetime(2017, 1, 11))):

            # Student #1 expresses interest in the class but still hasn't provided availability info.

            pict = PersonInClassTemplate.objects.create(
                person=stud1,
                class_template=ct,
                role=PersonInClassTemplate.ROLE_STUDENT,
            )
            pict.full_clean()

        self.assertEqual(ct.interested_student_count, 1)

        # +--------------+
        # | February 1st |
        # +--------------+
        with freeze_time(pytz.utc.localize(datetime(2017, 2, 1))):

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

            # We COULD now have enough interested students, depending on Student #1's (unknown) availability.
