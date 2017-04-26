# pylint: disable=E128

# Standard
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Union, List, Set, Optional
import math
import calendar

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

ConcreteEntity = Union['Person', 'Resource']
ConcreteEntityInClassTemplate = Union['PersonInClassTemplate', 'ResourceInClassTemplate']


# dt2ts is from http://stackoverflow.com/questions/5067218/get-utc-timestamp-in-python-with-datetime
def dt2ts(dt: datetime) -> TimeStamp:
    """Converts a datetime object to UTC timestamp. Naive datetime will be considered UTC."""
    return calendar.timegm(dt.utctimetuple())


class Entity(models.Model):

    def get_availability(self: ConcreteEntity, range_begin: date, range_end: date) -> IntervalSet:
        available = IntervalSet([])
        unavailable = IntervalSet([])
        for pos_tp in self.timepattern_set.filter(disposition=TimePattern.DISPOSITION_AVAILABLE).all():
            available += pos_tp.as_interval_set(range_begin, range_end)
        if available.empty():
            # If no positive timepatterns have been specified then we'll say that the pos part is infinite.
            # This makes it easy to specify things like "always available" and "always available except Fridays."
            # For the purpose of this method, "infite" translates to range_begin to range_end.
            range_begin_ts = dt2ts(pytz.utc.localize(datetime(range_begin.year, range_begin.month, range_begin.day)))
            range_end_ts = dt2ts(pytz.utc.localize(datetime(range_end.year, range_end.month, range_end.day)))
            available.add(closed(range_begin_ts, range_end_ts))
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

    def __str__(self):
        return str(self.django_user)


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
    """A situation in which people and resources are collectively available for some amount of time."""

    def __init__(self, eicts: List['EntityInClassTemplate'], timespan: Interval):
        self.entity_involvements = eicts
        self.timespan = timespan

    def __str__(self):
        result = " / ".join([str(eict.entity) for eict in self.entity_involvements]) + " / " + str(self.timespan)
        return result


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

    def is_actionable_solution(self, candidate_group_availability: GroupAvailability) -> bool:
        candidate_eicts = candidate_group_availability.entity_involvements  # type: List[EntityInClassTemplate]
        candidate_timespan = candidate_group_availability.timespan  # type: Interval

    # Get a entity count grouped by role:
        teacher_count = 0
        assistant_count = 0
        student_count = 0
        resource_count = 0

        for eict in candidate_eicts:
            assert eict.class_template == self
            if eict.entitys_role == PersonInClassTemplate.ROLE_TEACHER:
                # There can be more than one available teacher, even though only one will be needed.
                teacher_count += 1
            elif eict.entitys_role == PersonInClassTemplate.ROLE_ASSISTANT:
                assistant_count += 1
            elif eict.entitys_role == PersonInClassTemplate.ROLE_STUDENT:
                student_count += 1
            elif eict.entitys_role == ResourceInClassTemplate.ROLE_REQUIRED:
                resource_count += 1
            else:
                pass  # TODO: Log unrecognized role

        # Consider the teacher situation:
        if teacher_count == 0:
            return False

        # Consider the student situation:
        if student_count < self.min_students_required:
            return False

        # Consider the teaching assistant situation:
        assistants_must_handle = max(0, self.min_students_required - self.max_students_for_teacher)  # type: int
        assistants_required = math.ceil(assistants_must_handle / self.additional_students_per_ta)  # type: int
        if assistant_count < assistants_required:
            return False

        # For now, the logic for resources is that all of them are required.
        resources_required = self.resourceinclasstemplate_set.count()
        if resource_count < resources_required:
            return False

        # Consider the duration of this situation vs the duration of the class.
        candidate_duration = candidate_timespan.upper_value - candidate_timespan.lower_value  # type: DurationInSeconds
        if candidate_duration < self.duration*3600:
            return False

        # If we've made it this far, it means that we have a *potential* solution!
        # Whether or not it's an *actual* solution depends on RSVPs from people/resources.
        # The number of students that can be accomodated may depend on the TA RSVPs.
        return True

    def find_potential_solutions(self, range_begin: date, range_end: date) -> Set[GroupAvailability]:

        EiCT = EntityInClassTemplate

        class Event(object):
            def __init__(self, timestamp: TimeStamp, interval:Interval, islower:bool, eict:EiCT):
                self.timestamp = timestamp
                self.interval = interval
                self.islower = islower
                self.eict = eict

        # Make a sorted list of the availability events for all involved entities:
        eicts = []  # type: List[EiCT]
        events = []  # type: List[Event]
        eicts.extend(self.personinclasstemplate_set.all())
        eicts.extend(self.resourceinclasstemplate_set.all())
        for eict in eicts:  # EiCT
            ivalset = eict.person.get_availability(range_begin, range_end)  # type: IntervalSet
            for ival in ivalset:  # type: Interval
                lower_evt = Event(ival.lower_value, ival, True, eict)
                upper_evt = Event(ival.upper_value, ival, False, eict)
                events.append(lower_evt)
                events.append(upper_evt)
        events = sorted(events, key=lambda x: x.timestamp)  # type: List[Event]

        # Run through the events, finding simultaneously available involved entities.
        results = set()  # type: Set[GroupAvailability]
        currset = set()
        for event in events:  # type: Event

            # Adjust the current set as necessary.
            action = currset.add if event.islower else currset.remove
            action((event.eict, event.interval))

            # Find the intersection of the currset.
            candidate_timespan = open(NEGATIVE_INFINITY, INFINITY)  # type: Interval
            candidate_eicts = []
            for (eict, ival) in currset:
                candidate_timespan = candidate_timespan.intersect(ival)
                candidate_eicts.append(eict)
            ga = GroupAvailability(candidate_eicts, candidate_timespan)
            if self.is_actionable_solution(ga):
                results.add(ga)
                #print(ga)

        return results

    def note_timepattern_change(self):
        self.evaluate_situation()

    def note_personinclasstemplate_change(self):
        self.evaluate_situation()

    def note_resourceinclasstemplate_change(self):
        self.evaluate_situation()

    def __str__(self):
        return self.name


class EntityInClassTemplate(models.Model):

    class_template = models.ForeignKey(ClassTemplate, models.CASCADE, null=False, blank=False)

    @property
    def entity(self) -> ConcreteEntity:
        raise NotImplementedError()

    @property
    def entitys_role(self) -> str:
        raise NotImplementedError()

    class Meta:
        abstract = True


class PersonInClassTemplate(EntityInClassTemplate):

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
    role = models.CharField(max_length=3, choices=ROLE_CHOICES, null=False, blank=False)
    last_verified = models.DateField(auto_now_add=True, null=False, blank=False)

    @property
    def entity(self) -> Person:
        return self.person

    @property
    def entitys_role(self) -> str:
        return self.role

    def note_personinclasstemplate_change(self):
        self.class_template.note_personinclasstemplate_change()

    def __str__(self):
        return "{}/{}".format(self.role, self.person)


class ResourceInClassTemplate(EntityInClassTemplate):

    ROLE_REQUIRED = "REQ"

    resource = models.ForeignKey(Resource, models.CASCADE, null=False, blank=False)

    @property
    def entity(self) -> Resource:
        return self.resource

    @property
    def entitys_role(self) -> str:
        return "REQ"  # One, hard-coded role for resources. They're always required.

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
            inter_start = dt2ts(inter_start_dt)
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