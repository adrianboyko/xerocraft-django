
# Standard
import logging
import abc
from datetime import date, timedelta, datetime, time  # TODO: Replace datetime with django.utils.timezone
import re
from typing import Optional
from decimal import Decimal

# Third party
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

# Local
from members import models as mm
from abutils.deprecation import deprecated
from abutils.time import days_of_week_str, matches_weekday_of_month_pattern
from abutils.validators import positive_duration


class TimeWindowedObject(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def window_start_time(self) -> Optional[time]:
        """The time at which the window opens. E.g. the start time of a meeting. Can be None."""
        raise NotImplemented

    @abc.abstractmethod
    def window_duration(self) -> Optional[timedelta]:
        """How long the window stays open. E.g. the duration of a meeting. Can be None."""
        raise NotImplemented

    @abc.abstractmethod
    def window_sched_date(self) -> Optional[date]:
        """The date (if any) on which the window exists. Can be None."""
        raise NotImplemented

    @abc.abstractmethod
    def window_short_desc(self) -> str:
        """A short description of the activity that takes place during the time window. E.g name of meeting."""
        raise NotImplemented

    @abc.abstractmethod
    def window_deadline(self) -> Optional[date]:
        """If there'The last date onto which the window can extend"""
        raise NotImplemented

    def window_start_datetime(self):
        windate = self.window_sched_date()
        # If window_sched_date() is None, it means that the task can be done any day. So default to today.
        if windate is None:
            windate = datetime.now().date()
        return datetime.combine(windate, self.window_start_time())

    def window_end_datetime(self):
        return self.window_start_datetime() + self.window_duration()

    def in_daterange_now(self):
        """Determine whether we are currently in the date range for this object without considering time of day."""
        scheddate = self.window_sched_date()
        nowdate = datetime.now().date()
        deaddate = self.window_deadline()
        if deaddate is not None and nowdate > deaddate:
            return False  # The deadline for completing this work has passed, so we're out of the window.
        if scheddate is not None and scheddate != nowdate:
            return False  # The scheduled date has passed so we're out of the window.
        return True

    def in_window_now(self, start_leeway=timedelta(0), end_leeway=timedelta(0)):
        """Determine whether we are currently in the time range AND date range for this object."""

        if self.window_start_time() is not None and self.window_duration() is not None:
            now = datetime.now()
            start = self.window_start_datetime() + start_leeway
            end = self.window_end_datetime() + end_leeway
            if start > now:
                return False
            if end < now:
                return False

        return self.in_daterange_now()


class TaskMixin(models.Model):
    """Defines fields that are common between RecurringTaskTemplate and Task.
    When a task is created from the template, these fields are copied from the template to the task.
    Help text describes the fields in terms of their role in Task.
    """

    owner = models.ForeignKey(mm.Member, null=True, blank=True, related_name="owned_%(class)s",
        on_delete=models.SET_NULL,
        help_text="The member that asked for this task to be created or has taken responsibility for its content.<br/>This is almost certainly not the person who will claim the task and do the work.")

    instructions = models.TextField(max_length=2048, blank=True,
        help_text="Instructions for completing the task.")

    short_desc = models.CharField(max_length=40,
        help_text="A short description/name for the task.")

    max_workers = models.IntegerField(default=1, null=False, blank=False,
        help_text="The maximum number of members that can claim/work the task, often 1.")

    max_work = models.DurationField(null=False, blank=False,
        help_text="The max total amount of hours that can be claimed/worked for this task.")

    eligible_claimants = models.ManyToManyField(mm.Member, blank=True, related_name="claimable_%(class)s",
        help_text="Anybody chosen is eligible to claim the task.<br/>")

    anybody_is_eligible = models.BooleanField(default=False,
        help_text="Indicates whether the task is workable by ANYBODY. Use sparingly!")

    # Simplifying data model. Tags are currently only being used for the "anybody is eligible"
    # case so I'm replacing eligible_tags with an anybody_is_eligible bool, above.
    # eligible_tags = models.ManyToManyField(mm.Tag, blank=True, related_name="claimable_%(class)s",
    #     help_text="Anybody that has one of the chosen tags is eligible to claim the task.<br/>")

    reviewer = models.ForeignKey(mm.Member, null=True, blank=True, related_name="reviewable_%(class)s",
        on_delete=models.SET_NULL,
        help_text="If required, a member who will review the work once its completed.")

    work_start_time = models.TimeField(null=True, blank=True,
        help_text="The time at which work on the task must begin. If time doesn't matter, leave blank.")
    work_duration = models.DurationField(null=True, blank=True,
        validators=[positive_duration],
        help_text="Used with work_start_time to specify the time span over which work must occur. <br/>If work_start_time is blank then this should also be blank.")

    PRIO_HIGH = "H"
    PRIO_MED = "M"
    PRIO_LOW = "L"
    PRIORITY_CHOICES = [
        (PRIO_HIGH, "High"),
        (PRIO_MED, "Medium"),
        (PRIO_LOW, "Low")
    ]
    priority = models.CharField(max_length=1, default=PRIO_MED, choices=PRIORITY_CHOICES,
        help_text="The priority of the task, compared to other tasks.")

    should_nag = models.BooleanField(default=False,
        help_text="If true, people will be encouraged to work the task via email messages.")

    class Meta:
        abstract = True


class TemplateEligibleClaimants2(models.Model):

    template = models.ForeignKey('RecurringTaskTemplate', null=False,
        on_delete=models.CASCADE,  # Relation means nothing if the template is gone.
        help_text="The task in this relation.")

    member = models.ForeignKey(mm.Member,
        on_delete=models.CASCADE,  # Relation means nothing if the member is gone.
        help_text="The member in this relation.")

    TYPE_DEFAULT_CLAIMANT = "1ST"
    TYPE_ELIGIBLE_2ND     = "2ND"
    TYPE_ELIGIBLE_3RD     = "3RD"
    # NOTE: TYPE_DECLINED doesn't make sense at template level.
    TYPE_CHOICES = [
        (TYPE_DEFAULT_CLAIMANT, "Default Claimant"),
        (TYPE_ELIGIBLE_2ND,     "Eligible, 2nd String"),
        (TYPE_ELIGIBLE_3RD,     "Eligible, 3rd String"),
    ]
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, null=False, blank=False,
        help_text="The type of this relationship.")

    should_nag = models.BooleanField(default=False,
        help_text="If true, member will be encouraged to work instances of the template.")


class RecurringTaskTemplate(TaskMixin):
    """Uses two mutually exclusive methods to define a schedule for recurring tasks.
    (1) A 'day-of-week vs nth-of-month' matrix for schedules like "every first and third Thursday"
    (2) A 'repeat delay' value for schedules like "every 30 days"
    """

    start_date = models.DateField(help_text="Choose a date for the first instance of the recurring task.")
    active = models.BooleanField(default=True, help_text="Additional tasks will be created only when the template is active.")

    default_claimant = models.ForeignKey(mm.Member, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Some recurring tasks (e.g. classes) have a default a default claimant (e.g. the instructor).")

    eligible_claimants_2 = models.ManyToManyField(mm.Member, blank=True,
        related_name="claimable2_%(class)s",
        through = 'TemplateEligibleClaimants2',
        help_text="Anybody chosen is eligible to claim the task.<br/>")

    # Weekday of month:
    first = models.BooleanField(default=False)  # , help_text="Task will recur on first weekday in the month.")
    second = models.BooleanField(default=False)  # , help_text="Task will recur on second weekday in the month.")
    third = models.BooleanField(default=False)  # , help_text="Task will recur on third weekday in the month.")
    fourth = models.BooleanField(default=False)  # , help_text="Task will recur on fourth weekday in the month.")
    last = models.BooleanField(default=False)  # , help_text="Task will recur on last weekday in the month. This will be 4th or 5th weekday, depending on calendar.")
    every = models.BooleanField(default=False)  # , help_text="Task recur every week")

    # Day of week:
    monday = models.BooleanField(default=False)  # , help_text="Task will recur on Monday.")
    tuesday = models.BooleanField(default=False)  # , help_text="Task will recur on Tuesday.")
    wednesday = models.BooleanField(default=False)  # , help_text="Task will recur on Wednesday.")
    thursday = models.BooleanField(default=False)  # , help_text="Task will recur on Thursday.")
    friday = models.BooleanField(default=False)  # , help_text="Task will recur on Friday.")
    saturday = models.BooleanField(default=False)  # , help_text="Task will recur a Saturday.")
    sunday = models.BooleanField(default=False)  # , help_text="Task will recur a Sunday.")

    # Month of year:
    jan = models.BooleanField(default=True)
    feb = models.BooleanField(default=True)
    mar = models.BooleanField(default=True)
    apr = models.BooleanField(default=True)
    may = models.BooleanField(default=True)
    jun = models.BooleanField(default=True)
    jul = models.BooleanField(default=True)
    aug = models.BooleanField(default=True)
    sep = models.BooleanField(default=True)
    oct = models.BooleanField(default=True)
    nov = models.BooleanField(default=True)
    dec = models.BooleanField(default=True)

    # Every X days:
    repeat_interval = models.SmallIntegerField(null=True, blank=True, help_text="Minimum number of days between recurrences, e.g. 14 for every two weeks.")
    MDA_IGNORE = "I"
    MDA_SLIDE_SELF_AND_LATER = "S"
    MISSED_DATE_ACTIONS = [
        (MDA_IGNORE, "Don't do anything."),
        (MDA_SLIDE_SELF_AND_LATER, "Slide task and all later instances forward."),
    ]
    missed_date_action = models.CharField(max_length=1, null=True, blank=True,
        default=MDA_IGNORE, choices=MISSED_DATE_ACTIONS,
        help_text="What should be done if the task is not completed by the deadline date.")

    def clean(self):
        if self.work_start_time is not None and self.work_duration is None:
            raise ValidationError(_("You must specify a duration if you specify a start time."))
        if self.work_start_time is None and self.work_duration is not None:
            raise ValidationError(_("You must specify a work_start_time if you specify a duration."))
        if not (self.repeats_at_intervals() or self.repeats_on_certain_days()):
            raise ValidationError(_("Must specify 1) repetition at intervals or 2) repetition on certain days."))
        if self.repeats_at_intervals() and self.repeats_on_certain_days():
            raise ValidationError(_("Must not specify 1) repetition at intervals AND 2) repetition on certain days."))
        if self.last and self.fourth:  # REVIEW: Maybe it's OK
            raise ValidationError(_("Choose either fourth week or last week, not both."))
        if self.every and (self.first or self.second or self.third or self.fourth or self.last):
            raise ValidationError(_("If you choose 'every week' don't choose any other weeks."))

    # TODO: greatest_orig_sched_date(self):

    def greatest_scheduled_date(self):
        "Of the Tasks that correspond to this template, returns the greatest scheduled_date."

        if len(self.instances.all()) == 0:
            # Nothing is scheduled yet but nothing can be scheduled before start_date.
            # So, pretend that day before start_date is the greatest scheduled date.
            result = self.start_date + timedelta(days=-1)
            return result

        scheduled_dates = map(lambda x: x.scheduled_date, self.instances.all())
        return max(scheduled_dates)

    def date_matches_template(self, d: date):

        if self.repeats_at_intervals():
            return self.date_matches_template_intervals(d)

        if self.repeats_on_certain_days():
            return self.date_matches_template_certain_days(d)

    def date_matches_template_intervals(self, date_considered: date):
        last_date = self.greatest_scheduled_date()
        days_since = date_considered - last_date
        return days_since.days >= self.repeat_interval  # >= instead of == b/c of a bootstrapping scenario.

    def date_matches_template_certain_days(self, d: date):
        month_matches = (d.month == 1 and self.jan) \
            or (d.month == 2 and self.feb) \
            or (d.month == 3 and self.mar) \
            or (d.month == 4 and self.apr) \
            or (d.month == 5 and self.may) \
            or (d.month == 6 and self.jun) \
            or (d.month == 7 and self.jul) \
            or (d.month == 8 and self.aug) \
            or (d.month == 9 and self.sep) \
            or (d.month == 10 and self.oct) \
            or (d.month == 11 and self.nov) \
            or (d.month == 12 and self.dec)
        if not month_matches:
            return False
        return matches_weekday_of_month_pattern(self, d)

    def is_dow_chosen(self):
        return self.monday    \
            or self.tuesday   \
            or self.wednesday \
            or self.thursday  \
            or self.friday    \
            or self.saturday  \
            or self.sunday

    def is_ordinal_chosen(self):
        return self.first  \
            or self.second \
            or self.third  \
            or self.fourth \
            or self.last   \
            or self.every

    def is_month_chosen(self):
        return self.jan \
            or self.feb \
            or self.mar \
            or self.apr \
            or self.may \
            or self.jun \
            or self.jul \
            or self.aug \
            or self.sep \
            or self.oct \
            or self.nov \
            or self.dec

    def repeats_on_certain_days(self):
        return self.is_dow_chosen() and self.is_ordinal_chosen() and self.is_month_chosen()

    def repeats_at_intervals(self):
        return self.repeat_interval is not None

    def create_tasks(self, max_days_in_advance):
        """Creates/schedules new tasks from today or day after GSD (inclusive).
        Stops when scheduling a new task would be more than max_days_in_advance from current date.
        Does not create/schedule a task on date D if one already exists for date D.
        Does nothing if the template is not active.
        """

        if not self.active:
            return

        # Earliest possible date to schedule is "day after GSD" or "today", whichever is later.
        # Note that curr gets inc'ed at start of while, so we need "GSD" and "yesterday" here.
        gsd = self.greatest_scheduled_date()  # TODO: This should work with orig_sched_date, not scheduled_date
        yesterday = date.today()+timedelta(days=-1)
        curr = max(gsd, yesterday)
        stop = date.today() + timedelta(days=max_days_in_advance)
        logger = logging.getLogger("tasks")
        while curr < stop:
            curr += timedelta(days=+1)
            if self.date_matches_template(curr):

                # If task creation fails, log it and carry on.
                t = None  # type: Task
                try:
                    t = Task.objects.create(
                        recurring_task_template =self,
                        creation_date           =date.today(),
                        scheduled_date          =curr,
                        orig_sched_date         =curr,
                        # Copy mixin fields from template to instance:
                        owner                   =self.owner,
                        instructions            =Snippet.expand(self.instructions),
                        short_desc              =self.short_desc,
                        reviewer                =self.reviewer,
                        max_work                =self.max_work,
                        max_workers             =self.max_workers,
                        work_start_time         =self.work_start_time,
                        work_duration           =self.work_duration,
                        should_nag              =self.should_nag,
                        priority                =self.priority,
                        anybody_is_eligible     =self.anybody_is_eligible
                    )

                    # Many-to-many fields:
                    t.eligible_claimants.set(self.eligible_claimants.all())

                    if self.default_claimant is not None:
                        t.create_default_claim()

                    logger.info("Created %s on %s", self.short_desc, curr)

                except Exception as e:
                    logger.error("Couldn't create %s on %s because %s", self.short_desc, curr, str(e))
                    if t is not None:
                        t.delete()

    def recurrence_str(self):
        days_of_week = self.repeats_on_certain_days()
        intervals = self.repeats_at_intervals()
        if days_of_week and intervals:
            return "?"
        if (not days_of_week) and (not intervals):
            return "?"
        if days_of_week:
            return days_of_week_str(self)
        if intervals:
            if self.repeat_interval == 1:
                return "every day"
            else:
                return "every %d days" % self.repeat_interval
        return "X"
    recurrence_str.short_description = "Recurrence"

    def __str__(self):
        return "%s [%s]" % (self.short_desc, self.recurrence_str())

    class Meta:
        ordering = [
            'short_desc',
            '-sunday',
            '-monday',
            '-tuesday',
            '-wednesday',
            '-thursday',
            '-friday',
            '-saturday',
        ]


class Claim(models.Model, TimeWindowedObject):

    claimed_task = models.ForeignKey('Task', null=False,
        on_delete=models.CASCADE,  # The claim means nothing if the task is gone.
        help_text="The task against which the claim to work is made.")

    claiming_member = models.ForeignKey(mm.Member,
        on_delete=models.CASCADE,  # The claim means nothing if the member is gone.
        help_text="The member claiming the task.")

    stake_date = models.DateField(auto_now_add=True,
        help_text="The date on which the member staked this claim.")

    claimed_start_time = models.TimeField(null=True, blank=True,
        help_text="If the task specifies a start time and duration, this must fall within that time span. Otherwise it should be blank.")

    claimed_duration = models.DurationField(null=False, blank=False,
        help_text="The amount of work the member plans to do on the task.")

    date_verified = models.DateField(null=True, blank=True)

    STAT_CURRENT      = "C"  # Member has a current claim on the task.
    STAT_EXPIRED      = "X"  # Member didn't verify or finish the task while claimed, so member's claim has expired.
    STAT_QUEUED       = "Q"  # Member is interested in claiming task but it is already fully claimed.
    STAT_ABANDONED    = "A"  # Member had a claim on task but had to abandon it. E.g. "Something else came up."
    STAT_WORKING      = "W"  # The member is currently working the task, prob determined by checkin @ kiosk.
    STAT_DONE         = "D"  # The member has finished working the task, prob determined by checkout @ kiosk.
    STAT_UNINTERESTED = "U"  # The member doesn't want to claim the task. AKA "uninterested"
    CLAIM_STATUS_CHOICES = [
        (STAT_CURRENT,      "Current"),
        (STAT_EXPIRED,      "Expired"),
        (STAT_QUEUED,       "Queued"),
        (STAT_ABANDONED,    "Abandoned"),
        (STAT_WORKING,      "Working"),
        (STAT_DONE,         "Done"),
        (STAT_UNINTERESTED, "Uninterested"),
    ]
    status = models.CharField(max_length=1, choices=CLAIM_STATUS_CHOICES, null=False, blank=False,
        help_text="The status of this claim.")

    def clean(self):
        task = self.claimed_task; claim = self  # Makes it easier to read clean logic.
        if claim.claimed_duration <= timedelta(0):
            raise ValidationError(_("Duration must be greater than zero"))
        if task.work_start_time is not None and claim.claimed_start_time is None:
            raise ValidationError(_("Must specify the start time for this claim."))
        if task.work_start_time is None and claim.claimed_start_time is not None:
            pass  # REVIEW: I think this will be OK.

    def dbcheck(self):
        if False:  # TODO: Finish this check
            raise ValidationError(_("Task has a time window so claim must have a start time."))

    @staticmethod
    def sum_in_period(startDate, endDate):
        """ Sum up hours claimed per claimant during period startDate to endDate, inclusive. """
        claimants = {}
        for task in Task.objects.filter(scheduled_date__gte=startDate).filter(scheduled_date__lte=endDate):  # type: Task
            for claim in task.claim_set.all():  # type: Claim
                if claim.status == claim.STAT_CURRENT:
                    if claim.claiming_member not in claimants:
                        claimants[claim.claiming_member] = timedelta(0)
                    claimants[claim.claiming_member] += claim.claimed_duration
        return claimants

    # Implementation of TimeWindowedObject abstract methods:
    def window_start_time(self):
        return self.claimed_start_time

    def window_duration(self):
        return self.claimed_duration

    def window_sched_date(self):
        return self.claimed_task.scheduled_date

    def window_short_desc(self):
        return self.claimed_task.short_desc

    def window_deadline(self):
        return self.claimed_task.deadline

    def __str__(self):
        return "%s, %s, %s" % (
            self.claiming_member.friendly_name,
            self.status,
            self.claimed_task.short_desc
        )

    class Meta:
        unique_together = ('claiming_member', 'claimed_task')


class Work(models.Model):
    """Records work against a certain claim."""

    # Note: Time that work was done isn't very important at this point.  The member
    # is asserting that they worked inside whatever time constraints the task had.

    claim = models.ForeignKey('Claim', null=False, blank=False,
        on_delete=models.PROTECT,  # We don't want to lose data about work done.
        help_text="The claim against which the work is being reported.")

    work_date = models.DateField(null=False, blank=False,
        help_text="The date on which the work was started.")

    work_start_time = models.TimeField(
        null=True, blank=True,  # This is not available for all historical data.
        help_text="The time at which work began on the task.")

    work_duration = models.DurationField(null=True, blank=True,
        validators=[positive_duration],
        help_text="Time spent working the task. Only blank if work is in progress or worker forgot to check out.")

    witness = models.ForeignKey(mm.Member,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="A director or officer that witnessed the work.")

    def clean(self):
        work = self; claim = work.claim; task = claim.claimed_task  # Makes it easier to read logic, below:
        if work.work_duration is not None and work.work_duration > claim.claimed_duration:
            raise ValidationError(_("Can't report more work than was claimed."))

    def __str__(self):
        return "{} worked {} on {}".format(self.claim.claiming_member.username, self.work_duration, self.work_date)

    class Meta:
        verbose_name_plural = "Work"


class EligibleClaimant2(models.Model):

    task = models.ForeignKey('Task', null=False,
        on_delete=models.CASCADE,  # Relation means nothing if the task is gone.
        help_text="The task in this relation.")

    member = models.ForeignKey(mm.Member,
        on_delete=models.CASCADE,  # Relation means nothing if the member is gone.
        help_text="The member in this relation.")

    TYPE_DEFAULT_CLAIMANT = "1ST"
    TYPE_ELIGIBLE_2ND     = "2ND"
    TYPE_ELIGIBLE_3RD     = "3RD"
    TYPE_DECLINED         = "DEC"
    TYPE_CHOICES = [
        (TYPE_DEFAULT_CLAIMANT, "Default Claimant"),
        (TYPE_ELIGIBLE_2ND,     "Eligible, 2nd String"),
        (TYPE_ELIGIBLE_3RD,     "Eligible, 3rd String"),
        (TYPE_DECLINED,         "Will No Claim"),
    ]
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, null=False, blank=False,
        help_text="The type of this relationship.")

    should_nag = models.BooleanField(default=True,
        help_text="If true, member may receive email concerning the related task.")


class Task(TaskMixin, TimeWindowedObject):

    creation_date = models.DateField(null=False, default=date.today,
        help_text="The date on which this task was created in the database.")

    scheduled_date = models.DateField(null=True, blank=True,
        help_text="If appropriate, set a date on which the task must be performed.")

    orig_sched_date = models.DateField(null=True, blank=True,
        help_text="This is the first value that scheduled_date was set to. Required to avoid recreating a rescheduled task.")

    deadline = models.DateField(null=True, blank=True,
        help_text="If appropriate, specify a deadline by which the task must be completed.")

    depends_on = models.ManyToManyField('self', symmetrical=False, related_name="prerequisite_for",
        help_text="If appropriate, specify what tasks must be completed before this one can start.")

    eligible_claimants_2 = models.ManyToManyField(mm.Member, blank=True,
        related_name="claimable_tasks",
        through='EligibleClaimant2',
        help_text="Anybody chosen is eligible to claim the task.<br/>")

    claimants = models.ManyToManyField(mm.Member, through=Claim, related_name="tasks_claimed",
        help_text="The people who say they are going to work on this task.")

    # workers = models.ManyToManyField(mm.Member, through=Work, related_name="tasks_worked",
    #     help_text="The people who have actually posted hours against this task.")

    # TODO: If reviewer is None, setting status to REVIEWABLE should skip to DONE.
    STAT_ACTIVE     = "A"  # The task is (or will be) workable.
    STAT_REVIEWABLE = "R"  # Work is done and is awaiting review. Only meaningful when reviewer is not None.
    STAT_DONE       = "D"  # Work is complete and (if required) has passed review.
    STAT_CANCELED   = "C"  # Somebody decided that we will not work the task.
    TASK_STATUS_CHOICES = [
        (STAT_ACTIVE,     "Active"),
        (STAT_REVIEWABLE, "Reviewable"),
        (STAT_DONE,       "Done"),
        (STAT_CANCELED,   "Canceled"),
    ]
    status = models.CharField(max_length=1, choices=TASK_STATUS_CHOICES, null=False, blank=False, default=STAT_ACTIVE,
        help_text="The status of this task.")

    recurring_task_template = models.ForeignKey(RecurringTaskTemplate, null=True, blank=True, related_name="instances",
        on_delete=models.PROTECT)  # Existing code assumes that every task has a template.

    def clean(self):

        # TODO: Sum of claim hours should be <= duration if max_claimants==1. More complicated for >1.

        # TODO: Rewrite claimed-by check per model changes:
        # if self.prev_claimed_by == self.claimed_by:
        #     raise ValidationError(_("Member cannot claim a task they've previously claimed. Somebody else has to get a chance at it."))

        if self.work_duration is not None and self.work_duration <= timedelta(0):
            raise ValidationError(_("Duration must be greater than zero."))

        if self.max_work is not None and self.max_work <= timedelta(0):
            raise ValidationError(_("Duration must be greater than zero."))

        if self.recurring_task_template is not None and self.scheduled_date is None:
            raise ValidationError(_("A task corresponding to a ScheduledTaskTemplate must have a scheduled date."))

        if self.scheduled_date is not None and self.orig_sched_date is None:
            raise ValidationError(_("orig_sched_date must be set when scheduled_date is FIRST set."))

    @property
    def likely_worker(self) -> Optional[mm.Member]:
        """The member that is likely to work (or is already working) the task."""
        for claim in self.claim_set.all():  # type: Claim
            if claim.status in [claim.STAT_CURRENT, claim.STAT_WORKING, claim.STAT_DONE]:
                return claim.claiming_member
        return None

    @property
    def name_of_likely_worker(self) -> Optional[str]:
        """The friendly name of the member that is likely to work (or is already working) the task."""
        worker = self.likely_worker  # type: Optional[mm.Member]
        return worker.friendly_name if worker is not None else None

    def unclaimed_hours(self):
        """The grand total of hours still available to ALL WORKERS, considering other member's existing claims, if any."""
        unclaimed_hours = self.max_work
        for claim in self.claim_set.all():  # type: Claim
            if claim.status in [claim.STAT_CURRENT, claim.STAT_WORKING]:
                unclaimed_hours -= claim.claimed_duration
        return unclaimed_hours

    def max_claimable_hours(self):
        """The maximum number of hours that ONE WORKER can claim, considering other member's existing claims, if any."""
        if self.work_duration is None:
            return self.unclaimed_hours()
        else:
            return min(self.unclaimed_hours(), self.work_duration)

    def is_active(self):
        return self.status == self.STAT_ACTIVE

    @property
    def is_fully_claimed(self) -> bool:
        """
        Determine whether all the hours estimated for a task have been claimed by one or more members.
        :return: True or False
        """
        unclaimed_hours = self.unclaimed_hours()
        return unclaimed_hours == timedelta(0)

    def all_claims_verified(self) -> bool:
        return all(claim.date_verified is not None for claim in self.claim_set.all())

    STAFFING_STATUS_STAFFED     = "S"  # There is a verified current claim.
    STAFFING_STATUS_UNSTAFFED   = "U"  # There is no current claim.
    STAFFING_STATUS_PROVISIONAL = "P"  # There is an unverified current claim.
    STAFFING_STATUS_DONE        = "D"  # A claim is marked as done.

    def staffing_status(self) -> str:
        currClaims = self.claim_set.filter(status__in=[Claim.STAT_CURRENT, Claim.STAT_DONE])
        for claim in currClaims:  # type: Claim
            if claim.status == Claim.STAT_DONE:
                return Task.STAFFING_STATUS_DONE
        if self.is_fully_claimed:
            for claim in currClaims:  # type: Claim
                if claim.date_verified is None:
                    return Task.STAFFING_STATUS_PROVISIONAL
            return Task.STAFFING_STATUS_STAFFED
        else:
            return Task.STAFFING_STATUS_UNSTAFFED

    def all_eligible_claimants(self):
        """
        Determine all eligible claimants whether they're directly eligible by name or indirectly by tag
        :return: A set of Members
        """
        result = set(list(self.eligible_claimants.all()))
        return result

    @deprecated   # Use claimant_set instead
    def current_claimants(self):
        return self.claimant_set(Claim.STAT_CURRENT)

    def claimant_set(self, status):
        """
        Build the set of all claimants with a particular status.
        :return: A set of Members
        """
        result = set()
        for claim in self.claim_set.filter(status=status).all():
            result |= {claim.claiming_member}
        return result

    def create_default_claim(self):
        '''Create a claim assuming that other task info has already been initialized.'''

        # Short out if template doesn't specify a default claimant
        if self.recurring_task_template.default_claimant is None:
            return

        # Short out if default claimant already has a claim.
        def_claimant_claims = self.claim_set.filter(
            claiming_member=self.recurring_task_template.default_claimant,
        )
        if len(def_claimant_claims) > 0:
            return

        # Otherwise, create a claim for default claimant.
        duration = self.work_duration
        if duration is None:
            if self.max_workers != 1:
                raise RuntimeError("Not yet coded to deal with multiple workers.")
            else:
                duration = self.max_work
        Claim.objects.create(
            claiming_member=self.recurring_task_template.default_claimant,
            status=Claim.STAT_CURRENT,
            claimed_task=self,
            claimed_start_time=self.work_start_time,
            claimed_duration=duration
        )

    def all_future_instances(self):
        """Find other instances of the same template which are scheduled later than this instance."""
        all_future_instances = Task.objects.filter(
            recurring_task_template=self.recurring_task_template,
            scheduled_date__gt=self.scheduled_date,
            status=Task.STAT_ACTIVE
        )
        return all_future_instances

    def resync_with_template(self):
        templ = self.recurring_task_template

        # Values
        self.owner = templ.owner
        self.instructions = Snippet.expand(templ.instructions)
        self.short_desc = templ.short_desc
        self.reviewer = templ.reviewer
        self.max_work = templ.max_work
        self.max_workers = templ.max_workers
        self.work_start_time = templ.work_start_time
        self.work_duration = templ.work_duration
        self.should_nag = templ.should_nag
        self.priority = templ.priority
        self.anybody_is_eligible = templ.anybody_is_eligible

        # Sets
        self.eligible_claimants = templ.eligible_claimants.all()

        # Default claimant
        # Only delete claims that are unverified.
        unverified = self.claim_set.filter(status=Claim.STAT_CURRENT, date_verified__isnull=True)
        unverified.delete()
        # Then add a default claim if there aren't any left.
        if len(self.claimant_set(Claim.STAT_CURRENT)) == 0:
            self.create_default_claim()

        self.save()

    def all_future_instances_same_dow(self):
        """Find other instances of the same template which are scheduled later than this instance."""
        future_instances_same_dow = []
        for instance in self.all_future_instances():
            if instance.scheduled_weekday() == self.scheduled_weekday():
                future_instances_same_dow.append(instance)
        return future_instances_same_dow

    # TODO: Move this to TaskAdmin?
    def scheduled_weekday(self):
        return self.scheduled_date.strftime('%A') if self.scheduled_date is not None else '-'
        # return week[self.scheduled_date.weekday()] if self.scheduled_date is not None else '-'
    scheduled_weekday.short_description = "Weekday"

    # Implementation of TimeWindowedObject abstract methods:
    def window_start_time(self):
        return self.work_start_time

    def window_duration(self):
        return self.work_duration

    def window_sched_date(self):
        return self.scheduled_date

    def window_short_desc(self):
        return self.short_desc

    def window_deadline(self):
        return self.deadline

    def __str__(self):
        when = ""
        dead = ""
        result = "%s" % self.short_desc
        if self.scheduled_date is not None:
            when = ", " + self.scheduled_date.strftime('%a %b %d')
        if self.deadline is not None:
            dead = " [%s deadline]" % self.deadline
        return "%s%s%s" % (self.short_desc, when, dead)

    @property
    def full_desc(self): return str(self)

    class Meta:
        ordering = ['scheduled_date', 'work_start_time']
        # Intentionally using short_desc instead of recurringtasktemplate in constraint below.
        # In general, using short_desc will give a tighter constraint, crossing templates.
        unique_together = ('scheduled_date', 'short_desc', 'work_start_time')


class TaskNote(models.Model):

    # Note will be anonymous if author is null.
    author = models.ForeignKey(mm.Member, null=True, blank=True, related_name="task_notes_authored",
        on_delete=models.SET_NULL,  # Note will become anonymous if author is deleted.
        help_text="The member who wrote this note.")

    when_written = models.DateTimeField(null=False, auto_now_add=True,
        help_text="The date and time when the note was written.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the task. Questions, hints, problems, review feedback, etc.")

    task = models.ForeignKey(Task, related_name='notes',
        on_delete=models.CASCADE)  # The note is useless if the task is deleted.

    CRITICAL = "C"  # The note describes a critical issue that must be resolved. E.g. work estimate is too low.
    RESOLVED = "R"  # The note was previously listed as CRITICAL but the issue has been resolved.
    INFO = "I"  # The note is purely informational.
    NOTE_TYPE_CHOICES = [
        (CRITICAL, "Critical"),
        (RESOLVED, "Resolved"),
        (INFO, "Informational")
    ]
    status = models.CharField(max_length=1, choices=NOTE_TYPE_CHOICES)


class Nag(models.Model):

    when = models.DateTimeField(null=False, auto_now_add=True,
        help_text="The date and time when member was asked to work the task.")

    tasks = models.ManyToManyField(Task,
        help_text="The task that the member was asked to work.")

    claims = models.ManyToManyField(Claim,
        help_text="The claim that the member was asked to verify.")

    who = models.ForeignKey(mm.Member, null=True,
        on_delete=models.SET_NULL,  # The member might still respond to the nag email, so don't delete.
        help_text="The member who was nagged.")

    # Saving as MD5 provides some protection against read-only attacks.
    auth_token_md5 = models.CharField(max_length=32, null=False, blank=False,
        help_text="MD5 checksum of the random urlsafe base64 string used in the nagging email's URLs.")

    def __str__(self):
        return "%s %s, %ld tasks, %s" % (
            self.who.first_name,
            self.who.last_name,
            self.tasks.count(),
            self.when.strftime('%b %d'))


class Worker(models.Model):
    """ Settings per worker. """

    member = models.OneToOneField(mm.Member, null=False, unique=True, related_name="worker",
        help_text="This must point to the corresponding member.",
        on_delete=models.CASCADE)

    calendar_token = models.CharField(max_length=32, null=True, blank=True,
        help_text="Random hex string used to access calendar.")

    last_work_mtd_reported = models.DurationField(default=timedelta(0), null=False, blank=False,
        help_text="The most recent work MTD total reported to the worker.")

    should_include_alarms = models.BooleanField(default=False,
        help_text="Controls whether or not a worker's calendar includes alarms.")

    should_nag = models.BooleanField(default=False,
        help_text="Controls whether ANY nags should be sent to the worker.")

    should_report_work_mtd = models.BooleanField(default=False,
        help_text="Controls whether reports should be sent to worker when work MTD changes.")

    def populate_calendar_token(self):
        "Creates a calendar token if none exists, else does nothing."
        if self.calendar_token is None or len(self.calendar_token) == 0:
            # I'm arbitrarily choosing md5str, below, but the fact that it came from md5 doesn't matter.
            _, md5str = mm.Member.generate_auth_token_str(
                lambda t: Worker.objects.filter(calendar_token=t).count() == 0  # uniqueness test
            )
            self.calendar_token = md5str
            self.save()

    @property
    def first_name(self): return self.member.first_name

    @property
    def last_name(self): return self.member.last_name

    @property
    def username(self): return self.member.username

    @property
    def email(self): return self.member.email

    @property
    def is_active(self): return self.member.is_active

    def __str__(self) -> str:
        return self.username

    @classmethod
    def scheduled_receptionist(cls) -> Optional[mm.Member]:
        """Returns the currently scheduled receptionis, or None."""
        receptionTaskNames = [
            # TODO: Make this configurable. These are Xerocraft specific task names.
            "Open, Staff",
            "Open, Staff, Close",
            "Staff, Close",
        ]
        for claim in Claim.objects.filter(claimed_task__scheduled_date=date.today()).all():
            if claim.claimed_task.short_desc not in receptionTaskNames:
                continue
            dur_into_claim = datetime.now() - claim.window_start_datetime()  # type: timedelta
            if dur_into_claim > timedelta(0) and dur_into_claim < claim.claimed_duration:
                if claim.status in [Claim.STAT_CURRENT, Claim.STAT_WORKING]:
                    return claim.claiming_member

    class Meta:
        ordering = [
            'member__auth_user__first_name',
            'member__auth_user__last_name',
        ]


class WorkNote(models.Model):

    # Note will be anonymous if author is null.
    author = models.ForeignKey(mm.Member, null=True, blank=True, related_name="work_notes_authored",
        on_delete=models.SET_NULL,  # Note will become anonymous if author is deleted.
        help_text="The member who wrote this note.")

    when_written = models.DateTimeField(null=False, auto_now_add=True,
        help_text="The date and time when the note was written.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the work done.")

    work = models.ForeignKey(Work, related_name='notes',
        on_delete=models.CASCADE)  # Notes about work are useless if work is deleted.


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# UNAVAILABILITY
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class UnavailableDates(models.Model):

    who = models.ForeignKey(Worker, null=True, blank=True,
        on_delete=models.CASCADE,  # Unavailability info is uninteresting if the worker is deleted.
        help_text="The worker who will be unavailable.")

    start_date = models.DateField(
        help_text="The first date (inclusive) on which the person will be unavailable.")

    end_date = models.DateField(
        help_text="The last date (inclusive) on which the person will be unavailable.")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Text Snippets
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Snippet(models.Model):

    snippet_name_regex = '^[-a-zA-Z0-1]+$'
    snippet_ref_regex = r'\{\{[-a-zA-Z0-1]+\}\}'
    BAD_SNIPPET_REF_STR = "BAD_SNIPPET_REF"

    name = models.CharField(max_length=40, blank=False,
        help_text="The name of the snippet.",
        validators=[
            RegexValidator(
                snippet_name_regex,
                message="Name must only contain letters, numbers, and dashes.",
                code="invalid_name"
            )
        ]
    )

    description = models.CharField(max_length=128, blank=False,
        help_text="Short description of what the snippet is about.")

    text = models.TextField(max_length=2048, blank=False,
        help_text="The full text content of the snippet.")

    @staticmethod
    def expand(instr: str) -> str:
        while True:
            searchresult = re.search(Snippet.snippet_ref_regex, instr, flags=0)
            if searchresult is None:
                return instr
            snippet_ref = searchresult.group()
            snippet_name = snippet_ref.strip("{}")
            try:
                snippet = Snippet.objects.get(name=snippet_name)
                instr = instr.replace(snippet_ref, snippet.text)
            except Snippet.DoesNotExist:
                logger = logging.getLogger("tasks")
                logger.warning("%s is a bad snippet reference.", snippet_ref)
                instr = instr.replace(snippet_ref, Snippet.BAD_SNIPPET_REF_STR)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TIME ACCOUNTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class TimeAccountEntry(models.Model):

    explanation = models.CharField(max_length=80,
        null=False, blank=False,
        help_text="Explanation of this change.")

    worker = models.ForeignKey(Worker,
        null=False, blank=False,
        on_delete=models.CASCADE,  # If the member is deleted, any record of their free hours is uninteresting.
        help_text="The worker whose balance is changing.")

    when = models.DateTimeField(null=False, blank=False,
        default=timezone.now,
        help_text="Date/time of the change.")

    expires = models.DateTimeField(null=True, blank=True,
        default=None,
        help_text="For credits, the OPTIONAL date on which it expires.")

    change = models.DecimalField(max_digits=4, decimal_places=2,
        null=False, blank=False,
        help_text="The amount (in hours) added (positive) or deleted (negative).")

    work = models.ForeignKey(Work,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="For credits, a link to the associated work entry, if any.")

    play = models.ForeignKey(mm.Membership,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="For debits, a link to the associated membership, if any.")

    class Meta:
        ordering = ['when']
        verbose_name_plural = "time account entries"

    def __str__(self) -> str:
        change_str = "added to" if self.change > Decimal("0") else "removed from"
        return "{} hrs {} {}".format(self.change, change_str, self.worker.username)

    @property
    def balance(self) -> Decimal:
        log = TimeAccountEntry.objects.filter(
            worker=self.worker,
            when__lte=self.when,
            # expires__gt=self.effective No, we'll add an explicit Entry to reverse it.
        )
        balance = log.aggregate(models.Sum('change'))['change__sum']
        return balance

    def clean(self):
        if self.work is not None and self.play is not None:
            raise ValidationError("Specify ONE of work or play, or NEITHER. Not both.")
