# pylint: disable=C0330
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from datetime import date, timedelta, datetime
from members import models as mm
from decimal import Decimal
import logging
import abc
import nptime


class TimeWindowedObject(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def window_start_time(self):
        """The time at which the window opens. E.g. the start time of a meeting. Can be None."""
        return

    @abc.abstractmethod
    def window_duration(self):
        """How long the window stays open. E.g. the duration of a meeting. Can be None."""
        return

    @abc.abstractmethod
    def window_sched_date(self):
        """The date (if any) on which the window exists. Can be None."""
        return

    @abc.abstractmethod
    def window_short_desc(self):
        """A short description of the activity that takes place during the time window. E.g name of meeting."""
        return

    @abc.abstractmethod
    def window_deadline(self):
        """If there'The last date onto which the window can extend"""
        return

    def window_start_datetime(self):
        windate = self.window_sched_date()
        # If window_sched_date() is None, it means that the task can be done any day. So default to today.
        if windate is None: windate = datetime.now().date()
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
            if start > now: return False
            if end < now: return False

        return self.in_daterange_now()


def make_TaskMixin(dest_class_alias):
    """This function tunes the mix-in to avoid reverse accessor clashes.
-   The rest of the mix-in is identical for both Task and RecurringTaskTemplate.
-   """

    class TaskMixin(models.Model):
        """Defines fields that are common between RecurringTaskTemplate and Task.
        When a task is created from the template, these fields are copied from the template to the task.
        Help text describes the fields in terms of their role in Task.
        """

        owner = models.ForeignKey(mm.Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_"+dest_class_alias,
            help_text="The member that asked for this task to be created or has taken responsibility for its content.<br/>This is almost certainly not the person who will claim the task and do the work.")

        instructions = models.TextField(max_length=2048, blank=True,
            help_text="Instructions for completing the task.")

        short_desc = models.CharField(max_length=40,
            help_text="A short description/name for the task.")

        max_workers = models.IntegerField(default=1, null=False, blank=False,
            help_text="The maximum number of members that can claim/work the task, often 1.")

        max_work = models.DurationField(null=False, blank=False,
            help_text="The max total amount of hours that can be claimed/worked for this task.")

        eligible_claimants = models.ManyToManyField(mm.Member, blank=True, related_name="claimable_"+dest_class_alias,
            help_text="Anybody chosen is eligible to claim the task.<br/>")

        eligible_tags = models.ManyToManyField(mm.Tag, blank=True, related_name="claimable_"+dest_class_alias,
            help_text="Anybody that has one of the chosen tags is eligible to claim the task.<br/>")

        reviewer = models.ForeignKey(mm.Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewable"+dest_class_alias,
            help_text="If required, a member who will review the work once its completed.")

        # TODO: Maybe rename work_start_time -> window_start and work_duration -> window_size?
        work_start_time = models.TimeField(null=True, blank=True,
            help_text="The time at which work on the task must begin. If time doesn't matter, leave blank.")
        work_duration = models.DurationField(null=True, blank=True,
            help_text="Used with work_start_time to specify the time span over which work must occur. <br/>If work_start_time is blank then this should also be blank.")

        uninterested = models.ManyToManyField(mm.Member, blank=True, related_name="uninteresting_"+dest_class_alias,
            help_text="Members that are not interested in this item.")

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

        MDA_IGNORE = "I"
        MDA_SLIDE_SELF_AND_LATER = "S"
        MISSED_DATE_ACTIONS = [
            (MDA_IGNORE, "Don't do anything."),
            (MDA_SLIDE_SELF_AND_LATER, "Slide task and all later instances forward."),
        ]
        missed_date_action = models.CharField(max_length=1, null=True, blank= True,
            default=MDA_IGNORE, choices=MISSED_DATE_ACTIONS,
            help_text="What should be done if the task is not completed by the deadline date.")

        class Meta:
            abstract = True

    return TaskMixin


class RecurringTaskTemplate(make_TaskMixin("TaskTemplates")):
    """Uses two mutually exclusive methods to define a schedule for recurring tasks.
    (1) A 'day-of-week vs nth-of-month' matrix for schedules like "every first and third Thursday"
    (2) A 'repeat delay' value for schedules like "every 30 days"
    """

    start_date = models.DateField(help_text="Choose a date for the first instance of the recurring task.")
    active = models.BooleanField(default=True, help_text="Additional tasks will be created only when the template is active.")

    default_claimant = models.ForeignKey(mm.Member, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Some recurring tasks (e.g. classes) have a default a default claimant (e.g. the instructor).")

    # Weekday of month:
    first = models.BooleanField(default=False)  #, help_text="Task will recur on first weekday in the month.")
    second = models.BooleanField(default=False)  #, help_text="Task will recur on second weekday in the month.")
    third = models.BooleanField(default=False)  #, help_text="Task will recur on third weekday in the month.")
    fourth = models.BooleanField(default=False)  #, help_text="Task will recur on fourth weekday in the month.")
    last = models.BooleanField(default=False)  #, help_text="Task will recur on last weekday in the month. This will be 4th or 5th weekday, depending on calendar.")
    every = models.BooleanField(default=False)  #, help_text="Task recur every week")

    # Day of week:
    monday = models.BooleanField(default=False)  #, help_text="Task will recur on Monday.")
    tuesday = models.BooleanField(default=False)  #, help_text="Task will recur on Tuesday.")
    wednesday = models.BooleanField(default=False)  #, help_text="Task will recur on Wednesday.")
    thursday = models.BooleanField(default=False)  #, help_text="Task will recur on Thursday.")
    friday = models.BooleanField(default=False)  #, help_text="Task will recur on Friday.")
    saturday = models.BooleanField(default=False)  #, help_text="Task will recur a Saturday.")
    sunday = models.BooleanField(default=False)  #, help_text="Task will recur a Sunday.")

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
        if self.work_duration is not None and self.work_duration <= timedelta(0):
            raise ValidationError(_("Duration must be greater than zero."))

    # TODO: greatest_orig_sched_date(self):

    def greatest_scheduled_date(self):
        "Of the Tasks that correspond to this template, returns the greatest scheduled_date."

        if len(self.instances.all()) == 0:
            # Nothing is scheduled yet but nothing can be scheduled before start_date.
            # So, pretend that day before start_date is the greatest scheduled date.
            result = self.start_date + timedelta(days = -1)
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
        return days_since.days >= self.repeat_interval # >= instead of == b/c of a bootstrapping scenario.

    def date_matches_template_certain_days(self, d: date):

        def nth_xday(d):
            """ Return a value which indicates that date d is the nth <x>day of the month. """
            dom_num = d.day
            ord_num = 1
            while dom_num > 7:
                dom_num -= 7
                ord_num += 1
            return ord_num

        def is_last_xday(d):
            """ Return a value which indicates whether date d is the LAST <x>day of the month. """
            month = d.month
            d += timedelta(weeks = +1)
            return True if d.month > month else False

        month_matches = (d.month==1 and self.jan) \
            or (d.month==2 and self.feb) \
            or (d.month==3 and self.mar) \
            or (d.month==4 and self.apr) \
            or (d.month==5 and self.may) \
            or (d.month==6 and self.jun) \
            or (d.month==7 and self.jul) \
            or (d.month==8 and self.aug) \
            or (d.month==9 and self.sep) \
            or (d.month==10 and self.oct) \
            or (d.month==11 and self.nov) \
            or (d.month==12 and self.dec)
        if not month_matches: return False

        dow_num = d.weekday() # day-of-week number
        day_matches = (dow_num==0 and self.monday) \
            or (dow_num==1 and self.tuesday) \
            or (dow_num==2 and self.wednesday) \
            or (dow_num==3 and self.thursday) \
            or (dow_num==4 and self.friday) \
            or (dow_num==5 and self.saturday) \
            or (dow_num==6 and self.sunday)
        if not day_matches: return False  # Doesn't match template if day-of-week doesn't match.
        if self.every: return True  # Does match if it happens every week and the day-of-week matches.
        if is_last_xday(d) and self.last: return True # Check for last <x>day match.

        # Otherwise, figure out the ordinal and see if we match it.
        ord_num = nth_xday(d)
        ordinal_matches = (ord_num==1 and self.first) \
            or (ord_num==2 and self.second) \
            or (ord_num==3 and self.third) \
            or (ord_num==4 and self.fourth)

        return ordinal_matches

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

        if not self.active: return

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
                try:
                    t = None
                    t = Task.objects.create(
                        recurring_task_template =self,
                        creation_date           =date.today(),
                        scheduled_date          =curr,
                        orig_sched_date         =curr,
                        # Copy mixin fields from template to instance:
                        owner                   =self.owner,
                        instructions            =self.instructions,
                        short_desc              =self.short_desc,
                        reviewer                =self.reviewer,
                        missed_date_action      =self.missed_date_action,
                        max_work                =self.max_work,
                        max_workers             =self.max_workers,
                        work_start_time         =self.work_start_time,
                        work_duration           =self.work_duration,
                        should_nag              =self.should_nag,
                        priority                =self.priority,
                    )

                    # Many-to-many fields:
                    t.uninterested       =self.uninterested.all()
                    t.eligible_claimants =self.eligible_claimants.all()
                    t.eligible_tags      =self.eligible_tags.all()

                    if self.default_claimant is not None:
                        Claim.objects.create(
                            claiming_member=self.default_claimant,
                            status=Claim.STAT_CURRENT,
                            claimed_task=t,
                            claimed_start_time=self.work_start_time,
                            claimed_duration=self.work_duration
                        )
                    logger.info("Created %s on %s", self.short_desc, curr)

                except Exception as e:
                    logger.error("Couldn't create %s on %s because %s", self.short_desc, curr, str(e))
                    if t is not None: t.delete()

    def recurrence_str(self):
        days_of_week = self.repeats_on_certain_days()
        intervals = self.repeats_at_intervals()
        if days_of_week and intervals:
            return "?"
        if (not days_of_week) and (not intervals):
            return "?"
        if days_of_week:
            blank = '\u25CC'
            return "%s%s%s%s%s%s%s" % (
                "S" if self.sunday else blank,
                "M" if self.monday else blank,
                "T" if self.tuesday else blank,
                "W" if self.wednesday else blank,
                "T" if self.thursday else blank,
                "F" if self.friday else blank,
                "S" if self.saturday else blank,
            )
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
        on_delete=models.CASCADE, # The claim means nothing if the task is gone.
        help_text="The task against which the claim to work is made.")

    claiming_member = models.ForeignKey(mm.Member,
        help_text = "The member claiming the task.")

    stake_date = models.DateField(auto_now_add=True,
        help_text = "The date on which the member staked this claim.")

    claimed_start_time = models.TimeField(null=True, blank=True,
        help_text="If the task specifies a start time and duration, this must fall within that time span. Otherwise it should be blank.")

    claimed_duration = models.DurationField(null=False, blank=False,
        help_text="The amount of work the member plans to do on the task.")

    date_verified = models.DateField(null=True, blank=True)

    STAT_CURRENT   = "C"  # Member has a current claim on the task.
    STAT_EXPIRED   = "X"  # Member didn't finish the task while claimed, so member's claim has expired.
    STAT_QUEUED    = "Q"  # Member is interested in claiming task but it is already fully claimed.
    STAT_ABANDONED = "A"  # Member had a claim on task but had to abandon it.
    STAT_WORKING   = "W"  # The member is currently working the task, prob determined by checkin @ kiosk.
    STAT_DONE      = "D"  # The member has finished working the task, prob determined by checkout @ kiosk.
    CLAIM_STATUS_CHOICES = [
        (STAT_CURRENT,  "Current"),
        (STAT_EXPIRED,  "Expired"),
        (STAT_QUEUED,   "Queued"),
        (STAT_ABANDONED,"Abandoned"),
        (STAT_WORKING,  "Working"),
        (STAT_DONE,     "Done"),
    ]
    status = models.CharField(max_length=1, choices=CLAIM_STATUS_CHOICES, null=False, blank=False,
        help_text = "The status of this claim.")

    def clean(self):
        task = self.claimed_task; claim = self  # Makes it easier to read clean logic.
        if claim.claimed_duration <= timedelta(0):
            raise ValidationError(_("Duration must be greater than zero"))
        if task.work_start_time is not None and claim.claimed_start_time is None:
            raise ValidationError(_("Must specify the start time for this claim."))
        if task.work_start_time is None and claim.claimed_start_time is not None:
            pass  # REVIEW: I think this will be OK.

    @staticmethod
    def sum_in_period(startDate, endDate):
        """ Sum up hours claimed per claimant during period startDate to endDate, inclusive. """
        claimants = {}
        for task in Task.objects.filter(scheduled_date__gte=startDate).filter(scheduled_date__lte=endDate):
            for claim in task.claim_set.all():
                if claim.status == claim.STAT_CURRENT:
                    if claim.claiming_member not in claimants:
                        claimants[claim.claiming_member] = timedelta(0)
                    claimants[claim.claiming_member] += claim.claimed_duration
        return claimants

    # Implementation of TimeWindowedObject abstract methods:
    def window_start_time(self): return self.claimed_start_time
    def window_duration(self): return self.claimed_duration
    def window_sched_date(self): return self.claimed_task.scheduled_date
    def window_short_desc(self): return self.claimed_task.short_desc
    def window_deadline(self): return self.claimed_task.deadline

    def __str__(self):
        return "%s, %s" % (self.claiming_member.first_name, self.claimed_task.short_desc)

    class Meta:
        unique_together = ('claiming_member', 'claimed_task')


class Work(models.Model):
    """Records work against a certain claim."""

    # Note: Worker field removed since it's already available in claim.

    # Note: Time that work was done isn't very important at this point.  The member
    # is asserting that they worked inside whatever time constraints the task had.

    claim = models.ForeignKey('Claim', null=False, blank=False,
        on_delete=models.PROTECT, # We don't want to lose data about work done.
        help_text="The claim against which the work is being reported.")

    work_date = models.DateField(null=False, blank=False,
        help_text="The date on which the work was done.")

    work_duration = models.DurationField(null=False, blank=False,
        help_text = "The amount of time the member spent working.")

    def clean(self):
        work = self; claim = work.claim; task = claim.claimed_task  # Makes it easier to read logic, below:
        if work.work_duration <= timedelta(0):
            raise ValidationError(_("Duration must be greater than zero."))
        if work.work_duration > claim.claimed_duration:
            raise ValidationError(_("Can't report more work than was claimed."))

    class Meta:
        verbose_name_plural = "Work"


class Task(make_TaskMixin("Tasks"), TimeWindowedObject):

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

    claimants = models.ManyToManyField(mm.Member, through=Claim, related_name="tasks_claimed",
        help_text="The people who say they are going to work on this task.")

    #workers = models.ManyToManyField(mm.Member, through=Work, related_name="tasks_worked",
    #    help_text="The people who have actually posted hours against this task.")

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
        help_text = "The status of this task.")

    recurring_task_template = models.ForeignKey(RecurringTaskTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="instances")

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

    def unclaimed_hours(self):
        """The grand total of hours still available to ALL WORKERS, considering other member's existing claims, if any."""
        unclaimed_hours = self.max_work
        for claim in self.claim_set.all():
            if claim.status in [claim.STAT_CURRENT, claim.STAT_WORKING]:
                unclaimed_hours -= claim.claimed_duration
        return unclaimed_hours

    def max_claimable_hours(self):
        """The maximum number of hours that ONE WORKER can claim, considering other member's existing claims, if any."""
        if self.work_duration is None:
            return self.unclaimed_hours()
        else:
            return min(self.unclaimed_hours(), self.work_duration)

    def is_fully_claimed(self):
        """
        Determine whether all the hours estimated for a task have been claimed by one or more members.
        :return: True or False
        """
        unclaimed_hours = self.unclaimed_hours()
        return unclaimed_hours == timedelta(0)

    def all_eligible_claimants(self):
        """
        Determine all eligible claimants whether they're directly eligible by name or indirectly by tag
        :return: A set of Members
        """
        result = set()
        result |= set(list(self.eligible_claimants.all()))
        for tag in self.eligible_tags.all():
            result |= set(list(tag.members.all()))
        return result

    def current_claimants(self):
        """
        Determine the set of current claimants.
        :return: A set of Members
        """
        result = set()
        for claim in self.claim_set.all():
            if claim.status == claim.STAT_CURRENT:
                result |= set([claim.claiming_member])
        return result

    def all_future_instances(self):
        """Find other instances of the same template which are scheduled later than this instance."""
        all_future_instances = Task.objects.filter(
            recurring_task_template=self.recurring_task_template,
            scheduled_date__gt=self.scheduled_date,
            status=Task.STAT_ACTIVE
        )
        return all_future_instances

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
    def window_start_time(self): return self.work_start_time
    def window_duration(self): return self.work_duration
    def window_sched_date(self): return self.scheduled_date
    def window_short_desc(self): return self.short_desc
    def window_deadline(self): return self.deadline

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
        unique_together = ('scheduled_date', 'short_desc')


class TaskNote(models.Model):

    # Note will become anonymous if author is deleted or author is blank.
    author = models.ForeignKey(mm.Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="task_notes_authored",
        help_text="The member who wrote this note.")

    when_written = models.DateTimeField(null=False, auto_now_add=True,
        help_text="The date and time when the note was written.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the task. Questions, hints, problems, review feedback, etc.")

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes')

    CRITICAL = "C" # The note describes a critical issue that must be resolved. E.g. work estimate is too low.
    RESOLVED = "R" # The note was previously listed as CRITICAL but the issue has been resolved.
    INFO = "I" # The note is purely informational.
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

    # claims = models.ManyToManyField(Task,
    #     help_text="The claim that the member was asked to verify.")

    who = models.ForeignKey(mm.Member, null=True,
        on_delete=models.SET_NULL, # The member might still respond to the nag email, so don't delete.
        help_text = "The member who was nagged.")

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
        help_text="This must point to the corresponding member.")

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

    class Meta:
        ordering = [
            'member__auth_user__first_name',
            'member__auth_user__last_name',
        ]


class WorkNote(models.Model):

    # Note will become anonymous if author is deleted or author is blank.
    author = models.ForeignKey(mm.Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="work_notes_authored",
        help_text="The member who wrote this note.")

    when_written = models.DateTimeField(null=False, auto_now_add=True,
        help_text="The date and time when the note was written.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the work done.")

    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='notes')
