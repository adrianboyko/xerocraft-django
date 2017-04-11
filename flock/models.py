# pylint: disable=E128

# Standard
from decimal import Decimal
from datetime import date, datetime, timedelta

# Third-party
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

# Local

LONG_AGO = timezone.now()-timedelta(days=3650)


class Person(models.Model):
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
            # Only notify the ClassTemplates for which self's involvement doesn't have specific patterns.
            if len(pict.time_patterns) == 0:
                pict.class_template.note_timepattern_change()


class Resource(models.Model):
    """A room, a machine, etc."""

    name = models.CharField(max_length=80)
    short_description = models.CharField(max_length=240)
    long_description = models.TextField(max_length=2048)
    managers_email = models.EmailField(help_text="If blank, instructors will need to manually book the resource.")

    def note_timepattern_change(self):
        for rict in self.resourceinclasstemplate_set.all():  # type: ResourceInClassTemplate
            # Only notify the ClassTemplates for which self's involvement doesn't have specific patterns.
            if len(rict.time_patterns) == 0:
                rict.class_template.note_timepattern_change()


class ResourceControl(models.Model):

    TYPE_OWNER = "OWN"  # Controls availability of the resource and can grant 'manager' privileges.
    TYPE_MANAGER = "MGR"  # Same as 'owner' but can't grant 'manager' privileges.
    TYPE_CHOICES = [(TYPE_OWNER, "Owner"), (TYPE_MANAGER, "Manager")]

    person = models.ForeignKey(Person, models.CASCADE, null=False, blank=False)
    resource = models.ForeignKey(Resource, models.CASCADE, null=False, blank=False)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, null=False, blank=False)


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

    # If time_patterns is empty, ALL of the person's time patterns will be used.
    time_patterns = models.ManyToManyField('TimePattern')

    def note_personinclasstemplate_change(self):
        self.class_template.note_personinclasstemplate_change()


class ResourceInClassTemplate(models.Model):

    resource = models.ForeignKey(Resource, models.CASCADE, null=False, blank=False)
    class_template = models.ForeignKey(ClassTemplate, models.CASCADE, null=False, blank=False)

    # If time_patterns is empty, ALL of the resource's time patterns will be used.
    time_patterns = models.ManyToManyField('TimePattern')

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

        # Notify the ClassTemplates which are directly associated with this time pattern:
        for pict in self.personinclasstemplate_set.all():
            pict.class_template.note_timepattern_change()
        for rict in self.resourceinclasstemplate_set.all():
            rict.class_template.note_timepattern_change()

        # Notify the owner of this time pattern so it can notify other indirectly affected ClassTemplates:
        if self.person is not None:
            self.person.note_timepattern_change()
        if self.resource is not None:
            self.resource.note_timepattern_change()

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
