# pylint: disable=E128

# Standard
from decimal import Decimal

# Third-party
from django.db import models
from django.contrib.auth.models import User

# Local


class Entity(models.Model):
    """Entities can play a role in a Proposal or a Meeting."""
    pass


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
    entity = models.ForeignKey(Entity, models.CASCADE, null=False, blank=False)

    def __str__(self) -> str:
        return "{} {} @ {}:{} {} for {} hour{}".format(
            self.wom_dict, self.dow_dict,
            self.hour, self.minute, "AM" if self.morning else "PM",
            self.duration,
            "s" if self.duration != Decimal("1.0") else ""
        )


class Person(Entity):
    """An instructor, organizer, student, etc."""
    django_user = models.ForeignKey(User, models.CASCADE, null=False, blank=False)


class Resource(Entity):
    """A room, a machine, etc."""
    name = models.CharField(max_length=80)
    short_description = models.CharField(max_length=240)
    long_description = models.TextField(max_length=2048)
    managers_email = models.EmailField(help_text="If blank, instructors will need to manually book the resource.")


class ResourceControl(models.Model):

    TYPE_OWNER = "OWN"  # Controls availability of the resource and can grant 'manager' privs.
    TYPE_MANAGER = "MGR"  # Same as 'owner' but can't grant 'manager' privs.
    TYPE_CHOICES = [(TYPE_OWNER, "Owner"), (TYPE_MANAGER, "Manager")]

    person = models.ForeignKey(Person, models.CASCADE, null=False, blank=False)
    resource = models.ForeignKey(Resource, models.CASCADE, null=False, blank=False)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, null=False, blank=False)


class Proposal(models.Model):
    name = models.CharField(max_length=80)
    short_description = models.CharField(max_length=240)
    long_description = models.TextField(max_length=2048)
    min_students_required = models.IntegerField()
    max_students_allowed = models.IntegerField()
    max_students_for_teacher = models.IntegerField()
    additional_students_per_ta = models.IntegerField()


class EntityInProposal(models.Model):
    entity = models.ForeignKey(Entity, models.CASCADE, null=False, blank=False)
    proposal = models.ForeignKey(Proposal, models.CASCADE, null=False, blank=False)
    last_verified = models.DateField(auto_now_add=True, null=False, blank=False)


class PersonInProposal(EntityInProposal):

    ROLE_TEACHER = "TCH"
    ROLE_ASSISTANT = "HLP"
    ROLE_STUDENT = "STU"
    ROLE_CHOICES = [
        (ROLE_TEACHER, "Teacher"),
        (ROLE_ASSISTANT, "Teaching Assistant"),
        (ROLE_STUDENT, "Student"),
    ]
    role = models.CharField(max_length=3, choices=ROLE_CHOICES, null=False, blank=False)


class Meeting(models.Model):

    STATUS_VERIFYING = "SO?"
    STATUS_VERIFIED = "G2G"
    STATUS_FAILED = "BAD"
    STATUS_CHOICES = [
        (STATUS_VERIFYING, "Verifying participants and/or resources"),
        (STATUS_VERIFIED, "Everything is good to go"),
        (STATUS_FAILED, "People and/or resources weren't available"),
    ]

    proposal = models.ForeignKey(Proposal, models.CASCADE, null=False, blank=False)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=STATUS_VERIFYING)

    starts = models.DateTimeField(null=False, blank=False)
    duration = models.DecimalField(max_digits=4, decimal_places=2, null=False)

    asked_instructor = models.DateField(default=None)
    asked_assistants = models.DateField(default=None)
    asked_students = models.DateField(default=None)
    invoiced_students = models.DateField(default=None)
    asked_for_resources = models.DateField(default=None)  # Maybe at same time we invoice.

    instructor_is_go = models.BooleanField(default=False)
    assistants_are_go = models.BooleanField(default=False)
    students_are_go = models.BooleanField(default=False)  # I.e. more than min required.
    students_have_paid = models.BooleanField(default=False)  # I.e. more than min required.
    resources_are_go = models.BooleanField(default=False)

    seats_still_available = models.IntegerField()


class EntityInMeeting(models.Model):
    entity = models.ForeignKey(Entity, models.CASCADE, null=False, blank=False)
    meeting = models.ForeignKey(Meeting, models.CASCADE, null=False, blank=False)
    last_updated = models.DateField(null=False, blank=False, auto_now_add=True)


class PersonInMeeting(EntityInMeeting):

    STATUS_GOOD = "GUD"      # Time of meeting is good for person so we'll be asking them to attend.
    STATUS_BAD = "BAD"       # Time of meeting is bad for person but we *might* ask them to attend.
    STATUS_ASKED = "SO?"     # We have asked the person if they'd like to attend.
    STATUS_MAYBE = "MAB"     # We might nag them further to turn them yes or no.
    STATUS_NO = "NOP"        # The person will not attend.
    STATUS_YES = "YES"       # The person WILL attend. Instructors/assitants skip this state and go to APPROVED.
    STATUS_INVOICED = "INV"  # The person has been invoiced.
    STATUS_APPROVED = "G2G"  # The person has paid (if required) and is approved to attend the meeting.
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

    status = models.CharField(max_length=3, null=False)


class ResourceInMeeting(EntityInMeeting):

    STATUS_NOT_YET_RESERVED = "NOT"  # This state is for resources that need to be manually booked by instructor.
    STATUS_ASKED_MANAGERS = "SO?"  # This state is for resources that can be automatically booked via email.
    STATUS_RESERVED = "G2G"
    STATUS_CHOICES = [
        (STATUS_NOT_YET_RESERVED, "Not yet reserved"),
        (STATUS_ASKED_MANAGERS, "Waiting for approval"),
        (STATUS_RESERVED, "Resource is reserved"),
    ]

    resource = models.ForeignKey(Resource, models.CASCADE, null=False, blank=False)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, null=False, blank=False)
