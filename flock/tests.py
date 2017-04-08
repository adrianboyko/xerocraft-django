
# Standard
from datetime import date, timedelta
from decimal import Decimal

# Third-party
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

# Local
from .models import (
    ClassTemplate, ScheduledClass,
    Person, PersonInClassTemplate, PersonInScheduledClass,
    Resource, ResourceInClassTemplate, ResourceInScheduledClass,
    LONG_AGO,
)


def make_class_template() -> ClassTemplate:

    template = ClassTemplate.objects.create(
        min_students_required=4,
        max_students_allowed=9,
        max_students_for_teacher=4,
        additional_students_per_ta=4,
        duration=Decimal("2.0"),
    )  # type: ClassTemplate

    teacher_user = User.objects.create(username="t", first_name="The", last_name="Teacher")  # type:User
    teacher = Person.objects.create(django_user=teacher_user)  # type:Person

    assistant1_user = User.objects.create(username="a1", first_name="Assistant", last_name="#1")  # type: User
    assistant1 = Person.objects.create(django_user=assistant1_user)  # type:Person

    assistant2_user = User.objects.create(username="a2", first_name="Assistant", last_name="#2")  # type: User
    assistant2 = Person.objects.create(django_user=assistant2_user)  # type:Person

    student1_user = User.objects.create(username="s1", first_name="Student", last_name="#1")  # type: User
    student1 = Person.objects.create(django_user=student1_user)  # type:Person

    student2_user = User.objects.create(username="s2", first_name="Student", last_name="#2")  # type: User
    student2 = Person.objects.create(django_user=student2_user)  # type:Person

    PersonInClassTemplate.objects.create(person=teacher, class_template=template, role=PersonInClassTemplate.ROLE_TEACHER)
    PersonInClassTemplate.objects.create(person=assistant1, class_template=template, role=PersonInClassTemplate.ROLE_ASSISTANT)
    PersonInClassTemplate.objects.create(person=assistant2, class_template=template, role=PersonInClassTemplate.ROLE_ASSISTANT)
    PersonInClassTemplate.objects.create(person=student1, class_template=template, role=PersonInClassTemplate.ROLE_STUDENT)
    PersonInClassTemplate.objects.create(person=student2, class_template=template, role=PersonInClassTemplate.ROLE_STUDENT)

    return template


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


class TestStudentCounts(TestCase):

    def test_student_seats_total(self) -> None:
        class_template = make_class_template()  # type: ClassTemplate
        scheduled_class = class_template.instantiate(timezone.now())  # type: ScheduledClass

        self.assertEqual(scheduled_class.student_seats_total, 0)

        for pisc in scheduled_class.personinscheduledclass_set.all():
            pisc.status = PersonInScheduledClass.STATUS_APPROVED
            pisc.save()

        self.assertEqual(scheduled_class.student_seats_total, 9)
