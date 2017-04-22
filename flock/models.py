# pylint: disable=E128

# Standard
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Union, List, Set, Optional
import math

# Third-party
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from pyinter import Interval, IntervalSet, open, closed
from pyinter.extrema import INFINITY, NEGATIVE_INFINITY
import pytz

# Local
from abutils.time import *

# Types
TimeStamp = int
DurationInSeconds = int

LONG_AGO = timezone.now()-timedelta(days=3650)
FAR_FUTURE = timezone.now()+timedelta(days=3650)
DUR_15_MINS_IN_SECS = 15 * 60
ANALYSIS_RESOLUTION_IN_SECS = DUR_15_MINS_IN_SECS

ConcreteEntity = Union['Person', 'Resource']


class Entity(models.Model):

    def get_availability(self: ConcreteEntity, range_begin: date, range_end: date) -> IntervalSet:
        available = IntervalSet([])
        unavailable = IntervalSet([])
        for pos_tp in self.timepattern_set.filter(disposition=TimePattern.DISPOSITION_AVAILABLE).all():
            available += pos_tp.as_interval_set(range_begin, range_end)
        if available.empty():
            # If no positive timepatterns have been specified then we'll say that the pos part is infinite.
            # This makes it easy to specify things like "always available except Fridays."
            available = open(NEGATIVE_INFINITY, INFINITY)
        for neg_tp in self.timepattern_set.filter(disposition=TimePattern.DISPOSITION_UNAVAILABLE).all():
            unavailable += neg_tp.as_interval_set(range_begin, range_end)
        return available - unavailable

    class Meta:
        abstract = True


class Person(Entity):
    """An instructor, organizer, student, etc."""

    django_user = models.ForeignKey(User, models.CASCADE, null=False, blank=False)
    rest_time = models.IntegerField(default=1, help_text="Minimum days between classes.")

    @property
    def most_recent_class_start(self) -> date:
        try:
            pisc = PersonInScheduledClass.objects\
                .filter(
                  person=self,
                  scheduled_class__starts__lt=timezone.now(),
                  scheduled_class__status=ScheduledClass.STATUS_VERIFIED
                )\
                .latest('scheduled_class__starts')  # type: PersonInScheduledClass
            return pisc.scheduled_class.starts
        except PersonInScheduledClass.DoesNotExist:
            return LONG_AGO

    @property
    def is_resting(self) -> bool:
        time_since_last_class = timezone.now() - self.most_recent_class_start
        return time_since_last_class < timedelta(days=self.rest_time)

    def note_timepattern_change(self):
        for pict in self.personinclasstemplate_set.all():  # type: PersonInClassTemplate
            pict.class_template.note_timepattern_change()


class Resource(Entity):
    """A room, a machine, etc."""

    name = models.CharField(max_length=80)
    short_description = models.CharField(max_length=240)
    long_description = models.TextField(max_length=2048)
    managers_email = models.EmailField(help_text="If blank, instructors will need to manually book the resource.")

    def note_timepattern_change(self):
        for rict in self.resourceinclasstemplate_set.all():  # type: ResourceInClassTemplate
            rict.class_template.note_timepattern_change()


class ResourceControl(models.Model):

    TYPE_OWNER = "OWN"  # Controls availability of the resource and can grant 'manager' privileges.
    TYPE_MANAGER = "MGR"  # Same as 'owner' but can't grant 'manager' privileges.
    TYPE_CHOICES = [(TYPE_OWNER, "Owner"), (TYPE_MANAGER, "Manager")]

    person = models.ForeignKey(Person, models.CASCADE, null=False, blank=False)
    resource = models.ForeignKey(Resource, models.CASCADE, null=False, blank=False)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, null=False, blank=False)


class GroupAvailability(object):
    """A situation in which people and resources are collectively available."""

    def __init__(self,
      available_picts: List['PersonInClassTemplate'],
      available_ricts: List['ResourceInClassTemplate'],
      start: TimeStamp):
        self.available_picts = available_picts
        self.available_ricts = available_ricts
        self.start = start  # type: TimeStamp
        self.end = None  # type: Optional[TimeStmamp]  # Situation starts as a point in time.
        self.teachers_needed = None  # type: Optional[int]
        self.assistants_needed = None  # type: Optional[int]
        self.students_needed = None  # type: Optional[int]
        self.resources_available = None  # type: Optional[bool]
        self.is_potential_solution = None  # type: Optional[bool]

    @property
    def duration(self) -> Optional[DurationInSeconds]:
        if self.end is None:
            return None
        else:
            return self.end - self.start

    def evaluate(self, ct: 'ClassTemplate'):

        # Get a person count grouped by role:
        teacher_count = 0
        assistant_count = 0
        student_count = 0
        for pict in self.available_picts:
            assert pict.class_template == ct
            if pict.role == pict.ROLE_TEACHER:
                # There can be more than one available teacher, even though only one will be needed.
                teacher_count += 1
            elif pict.role == pict.ROLE_ASSISTANT:
                assistant_count += 1
            elif pict.role == pict.ROLE_STUDENT:
                student_count += 1

        # Consider the teacher situation:
        if teacher_count == 0:
            self.teachers_needed = 1
            # There's no point in considering anything else if there's no teacher, so:
            return
        else:
            self.teachers_needed = 0

        # Consider the student situation:
        self.students_needed = max(0, ct.min_students_required - student_count)
        if self.students_needed > 0:
            # There's no point in considering anything else if we don't have enough students, so:
            return

        # Consider the teaching assistant situation:
        assistants_must_handle = max(0, ct.min_students_required - ct.max_students_for_teacher)
        self.assistants_needed = math.ceil(assistants_must_handle / ct.additional_students_per_ta)
        if self.assistants_needed > assistant_count:
            # There's no point in considering anything else if we don't have enough TAs, so:
            return

        # For now, the logic for resources is that all of them are required.
        required_resources = set([x.resource for x in ct.resourceinclasstemplate_set.all()])
        available_resources = set([x.resource for x in self.available_ricts])
        self.resources_available = required_resources == available_resources
        if not self.resources_available:
            # There's no point in considering anything else if we don't have the req'd resources, so:
            return

        # Consider the duration of this situation vs the duration of the class.
        self.is_potential_solution = self.duration >= ct.duration*3600
        if not self.is_potential_solution:
            return

        # If we've made it this far, it means that we have a *potential* solution!
        # Whether or not it's an *actual* solution depends on RSVPs from people/resources.
        # The number of students that can be accomodated may depend on the TA RSVPs.


class ClassTemplate(models.Model):

    name = models.CharField(max_length=80, null=False, blank=False)
    short_description = models.CharField(max_length=240, null=False, blank=False)
    long_description = models.TextField(max_length=2048, null=False, blank=False)
    duration = models.DecimalField(max_digits=4, decimal_places=2, null=False, blank=False)
    min_students_required = models.IntegerField()
    max_students_allowed = models.IntegerField()
    max_students_for_teacher = models.IntegerField()
    additional_students_per_ta = models.IntegerField()

    def instantiate(self, scheduled_start: datetime) -> 'ScheduledClass':
        sc = ScheduledClass.objects.create(
            class_template=self,
            starts=scheduled_start,
            duration=self.duration,
            status=ScheduledClass.STATUS_VERIFYING,
        )
        for pict in self.personinclasstemplate_set.all():
            PersonInScheduledClass.objects.create(
                scheduled_class=sc,
                person=pict.person,
                role=pict.role
            )
        return sc

    @property
    def interested_student_count(self) -> int:
        return self.personinclasstemplate_set.filter(role=PersonInClassTemplate.ROLE_STUDENT).count()

    def evaluate_situation(self):
        if self.interested_student_count > self.min_students_required:
            pass

    def find_potential_solutions(self, range_begin: date, range_end: date) -> Set[GroupAvailability]:

        class PiCT(PersonInClassTemplate):
            """Subclass adds a few fields that are specific to this method."""
            def __init__(self):
                super().__init__()
                self.run_begin = None  # type: TimeStamp
                self.run_end = None  # type: TimeStamp
                self.availability = None  # type: IntervalSet

        class RiCT(ResourceInClassTemplate):
            """Currently just an alias but might be used for additional method-specific fields."""
            pass

        picts = set()  # type: Set[PiCT]
        for pict in self.personinclasstemplate_set.all():  # type: PiCT
            pict.availability = pict.person.get_availability(range_begin, range_end)
            picts.add(pict)

        ricts = set()  # type: Set[RiCT]
        for rict in self.resourceinclasstemplate_set.all():  # type: RiCT
            rict.availability = rict.resource.get_availability(range_begin, range_end)
            ricts.add(rict)

        begin_dt = datetime(range_begin.year, range_begin.month, range_begin.day, 0, 0, 0)  # type: datetime
        end_dt = datetime(range_end.year, range_end.month, range_end.day, 23, 59, 59)  # type: datetime
        begin = int(pytz.utc.localize(begin_dt).timestamp())  # type: TimeStamp
        end = int(pytz.utc.localize(end_dt).timestamp())  # type: TimeStamp

        results = set()  # type: Set[GroupAvailability]
        runners = set()  # type: Set[PiCT]

        for t in range(begin, end, ANALYSIS_RESOLUTION_IN_SECS):

            # For now, we'll only consider cases times when ALL the resources are available.
            # I.e. This doesn't handle the cases such as: ONE of the TWO suitable classrooms are available.
            ricts_available = set(filter(lambda x: t in x.availability, ricts))  # type: Set[RiCT]
            if ricts_available != ricts:
                continue

            picts_available = set(filter(lambda x: t in x.availability, picts))  # type: Set[PiCT]
            new_runners = picts_available - runners  # type: Set[PiCT]
            done_runners = runners - picts_available  # type: Set[PiCT]
            runners = runners.union(new_runners) - done_runners

            for new_runner in new_runners:  # type: PiCT
                new_runner.run_begin = t

            start_times_for_done_runners = set()  # type: Set[TimeStamp]
            for done_runner in done_runners:  # type: PiCT
                done_runner.run_end = t - ANALYSIS_RESOLUTION_IN_SECS  # Last availability was ONE TICK AGO.
                start_times_for_done_runners.add(done_runner.run_begin)

            for start_time in start_times_for_done_runners:  # type: TimeStamp
                picts_in_span = set()
                for done_runner in done_runners:  # type: PiCT
                    if start_time in done_runner.availability:
                        picts_in_span.add(done_runner)
                ga = GroupAvailability(list(picts_in_span), list(ricts), start_time)
                ga.end = t - ANALYSIS_RESOLUTION_IN_SECS  # Last availability was ONE TICK AGO.
                ga.evaluate(self)
                if ga.is_potential_solution:
                    results.add(ga)

        # TODO: Also run through loop logic with hardcoded new_runners = {} and done_runners = runners.
        # TODO: Doing so should find any boundary solutions on the end of the range.
        return results

    def note_timepattern_change(self):
        self.evaluate_situation()

    def note_personinclasstemplate_change(self):
        self.evaluate_situation()

    def note_resourceinclasstemplate_change(self):
        self.evaluate_situation()

    def __str__(self):
        return self.name


class PersonInClassTemplate(models.Model):

    ROLE_ORGANIZER = "ORG"  # Might want to organize templates before there's a teacher, to collect students.
    ROLE_TEACHER = "TCH"
    ROLE_ASSISTANT = "HLP"
    ROLE_STUDENT = "STU"
    ROLE_CHOICES = [
        (ROLE_TEACHER, "Teacher"),
        (ROLE_ASSISTANT, "Teaching Assistant"),
        (ROLE_STUDENT, "Student"),
    ]

    person = models.ForeignKey(Person, models.CASCADE, null=False, blank=False)
    class_template = models.ForeignKey(ClassTemplate, models.CASCADE, null=False, blank=False)
    role = models.CharField(max_length=3, choices=ROLE_CHOICES, null=False, blank=False)
    last_verified = models.DateField(auto_now_add=True, null=False, blank=False)

    def note_personinclasstemplate_change(self):
        self.class_template.note_personinclasstemplate_change()


class ResourceInClassTemplate(models.Model):

    resource = models.ForeignKey(Resource, models.CASCADE, null=False, blank=False)
    class_template = models.ForeignKey(ClassTemplate, models.CASCADE, null=False, blank=False)

    def note_resourceinclasstemplate_change(self):
        self.class_template.note_resourceinclasstemplate_change()


class TimePattern(models.Model):
    """Sets of time patterns declare the availability of Entities."""
    # Availability is specified as a set of available times MINUS a set of unavailable times.

    DISPOSITION_AVAILABLE = "AV"
    DISPOSITION_UNAVAILABLE = "UN"
    DISPOSITION_CHOICES = [
        (DISPOSITION_AVAILABLE, "available"),
        (DISPOSITION_AVAILABLE, "unavailable")
    ]

    DOW_MON = "Mo"
    DOW_TUE = "Tu"
    DOW_WED = "We"
    DOW_THU = "Th"
    DOW_FRI = "Fr"
    DOW_SAT = "Sa"
    DOW_SUN = "Su"
    DOW_CHOICES = [
        (DOW_MON, "Monday"),
        (DOW_TUE, "Tuesday"),
        (DOW_WED, "Wednesday"),
        (DOW_THU, "Thursday"),
        (DOW_FRI, "Friday"),
        (DOW_SAT, "Saturday"),
        (DOW_SUN, "Sunday"),
    ]

    WOM_1ST = "1"
    WOM_2ND = "2"
    WOM_3RD = "3"
    WOM_4TH = "4"
    WOM_LAST = "L"
    WOM_EVERY = "E"
    WOM_CHOICES = [
        (WOM_1ST, "1st"),
        (WOM_2ND, "2nd"),
        (WOM_3RD, "3rd"),
        (WOM_4TH, "4th"),
        (WOM_LAST, "last"),
        (WOM_EVERY, "every"),
    ]

    dow_dict = dict(DOW_CHOICES)
    wom_dict = dict(WOM_CHOICES)

    disposition = models.CharField(max_length=2, choices=DISPOSITION_CHOICES, null=False, blank=False)
    wom = models.CharField(max_length=1, choices=WOM_CHOICES, null=False, blank=False)
    dow = models.CharField(max_length=2, choices=DOW_CHOICES, null=False, blank=False)
    hour = models.IntegerField(choices=[(i, i) for i in range(1, 13)], null=False, blank=False)
    minute = models.IntegerField(choices=[(i, i) for i in range(0, 60)], null=False, blank=False)
    morning = models.BooleanField(default=False)
    duration = models.DecimalField(max_digits=3, decimal_places=2, null=False, blank=False)

    # Each time pattern belongs to a specific Person or Resource. Only set one of these two:
    person = models.ForeignKey(Person, models.CASCADE, null=True, blank=True)
    resource = models.ForeignKey(Resource, models.CASCADE, null=True, blank=True)

    def note_timepattern_change(self):

        # Notify the owner of this time pattern so it can notify other indirectly affected ClassTemplates:
        if self.person is not None:
            self.person.note_timepattern_change()
        if self.resource is not None:
            self.resource.note_timepattern_change()

    def as_interval_set(self, start: date, finish: date) -> IntervalSet:
        """
            Return an interval set representation of the TimePattern between two bounds.
            
            The intervals are closed and expressed using Unix timestamps (the number of seconds 
            since 1970-01-01 UTC, not counting leap seconds). Since TimePattern defines an infinite
            sequence of intervals across all time, this function takes a starting date and ending date.
            Only those intervals with start times that fall between the starting and ending date are 
            returned in the interval set result.            
        """
        dow_dict = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}

        # REVIEW: Is there a more efficient implementation that uses dateutil.rrule?

        epoch = pytz.utc.localize(datetime(1970, 1, 1, 0, 0, 0))
        tz = timezone.get_current_timezone()
        iset = IntervalSet([])  # type: IntervalSet
        d = start - timedelta(days=1)  # type: date
        while d <= finish:
            d = d + timedelta(days=1)

            if dow_dict[self.dow] != d.weekday():
                continue

            if self.wom == self.WOM_LAST:
                if not is_last_xxxday_of_month(d):
                    continue

            if self.wom not in [self.WOM_LAST, self.WOM_EVERY]:
                nth = int(self.wom)
                if not is_nth_xxxday_of_month(d, nth):
                    continue

            am_pm_adjust = 0 if self.morning else 12
            inter_start_dt = tz.localize(datetime(d.year, d.month, d.day, self.hour+am_pm_adjust, self.minute))
            inter_start = int((inter_start_dt - epoch).total_seconds())
            inter_end = int(inter_start + self.duration*3600)
            iset.add(closed(inter_start, inter_end))

        return iset

    def clean(self):
        p = self.person is None
        r = self.resource is None
        if p == r:
            raise ValidationError(_("TimePattern must be owned by a Person XOR a Resource!"))

    def __str__(self) -> str:
        return "{} {} @ {}:{} {} for {} hour{}".format(
            self.wom_dict[self.wom], self.dow_dict[self.dow],
            self.hour, self.minute, "AM" if self.morning else "PM",
            self.duration,
            "s" if self.duration != Decimal("1.0") else ""
        )


class ScheduledClass(models.Model):

    STATUS_VERIFYING = "SO?"
    STATUS_VERIFIED = "G2G"
    STATUS_FAILED = "BAD"
    STATUS_CHOICES = [
        (STATUS_VERIFYING, "Verifying participants and/or resources"),
        (STATUS_VERIFIED, "Everything is good to go"),
        (STATUS_FAILED, "People and/or resources weren't available"),
    ]

    class_template = models.ForeignKey(ClassTemplate, models.CASCADE, null=False, blank=False)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=STATUS_VERIFYING)
    starts = models.DateTimeField(null=False, blank=False)
    duration = models.DecimalField(max_digits=4, decimal_places=2, null=False, blank=False)

    asked_instructor = models.DateField(default=None, null=True, blank=True)
    asked_assistants = models.DateField(default=None, null=True, blank=True)
    asked_students = models.DateField(default=None, null=True, blank=True)
    invoiced_students = models.DateField(default=None, null=True, blank=True)
    asked_for_resources = models.DateField(default=None, null=True, blank=True)  # Maybe at same time we invoice.

    @property
    def student_seats_total(self) -> int:
        """Determine how many seats are available given instructor and assistant statuses. Varies with time."""
        piscs = PersonInScheduledClass.objects.filter(
            scheduled_class=self,
            role__in=[PersonInClassTemplate.ROLE_TEACHER, PersonInClassTemplate.ROLE_ASSISTANT],
            status=PersonInScheduledClass.STATUS_APPROVED,
        ).all()
        total = 0
        for pisc in piscs:  # type: PersonInScheduledClass
            if pisc.role == PersonInClassTemplate.ROLE_ASSISTANT:
                total += self.class_template.additional_students_per_ta
            if pisc.role == PersonInClassTemplate.ROLE_TEACHER:
                total += self.class_template.max_students_for_teacher
        return min(total, self.class_template.max_students_allowed)

    @property
    def student_seats_taken(self) -> int:
        if self.status == ScheduledClass.STATUS_FAILED:
            return 0


class PersonInScheduledClass(models.Model):

    STATUS_GOOD = "GUD"      # Time of class is good for person so we'll be asking them to attend.
    STATUS_BAD = "BAD"       # Time of class is bad for person but we *might* ask them to attend.
    STATUS_ASKED = "SO?"     # We have asked the person if they'd like to attend.
    STATUS_MAYBE = "MAB"     # We might nag them further to turn them yes or no.
    STATUS_NO = "NOP"        # The person will not attend.
    STATUS_YES = "YES"       # The person WILL attend. Instructors/assitants skip this state and go to APPROVED.
    STATUS_INVOICED = "INV"  # The person has been invoiced.
    STATUS_APPROVED = "G2G"  # The person has paid (if required) and is approved to attend the class.
    STATUS_CHOICES = [
        (STATUS_GOOD, "Will ask person to attend"),
        (STATUS_BAD, "Might ask person to attend"),
        (STATUS_ASKED, "Person has been asked if they'll attend"),
        (STATUS_MAYBE, "Person says that they MIGHT attend"),
        (STATUS_NO, "Person says that they will NOT attend"),
        (STATUS_YES, "Person says that they WILL attend"),
        (STATUS_INVOICED, "Person has been invoiced"),
        (STATUS_APPROVED, "Person has been approved to attend")
    ]

    person = models.ForeignKey(Person, models.CASCADE, null=False, blank=False)
    scheduled_class = models.ForeignKey(ScheduledClass, models.CASCADE, null=False, blank=False)
    last_updated = models.DateField(null=False, blank=False, auto_now_add=True)
    status = models.CharField(max_length=3, null=False)

    # Role, below, should be initially copied from the corresponding ClassTemplate.
    # The role can be modified later, if required, e.g. if an assistant will sub for the instructor.
    role = models.CharField(max_length=3, choices=PersonInClassTemplate.ROLE_CHOICES, null=False)


class ResourceInScheduledClass(models.Model):

    STATUS_NOT_YET_RESERVED = "NOT"  # This state is for resources that need to be manually booked by instructor.
    STATUS_ASKED_MANAGERS = "SO?"  # This state is for resources that can be automatically booked via email.
    STATUS_RESERVED = "G2G"
    STATUS_CHOICES = [
        (STATUS_NOT_YET_RESERVED, "Not yet reserved"),
        (STATUS_ASKED_MANAGERS, "Waiting for approval"),
        (STATUS_RESERVED, "Resource is reserved"),
    ]

    resource = models.ForeignKey(Resource, models.CASCADE, null=False, blank=False)
    scheduled_class = models.ForeignKey(ScheduledClass, models.CASCADE, null=False, blank=False)
    last_updated = models.DateField(null=False, blank=False, auto_now_add=True)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, null=False, blank=False)


# class IntervalOfAvailability(models.Model):
#     pass