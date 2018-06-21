
# Standard
import datetime
from decimal import Decimal

# Third Party
from django.contrib import admin
from django.contrib.admin.views import main
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from nptime import nptime
from reversion.admin import VersionAdmin

# Local
from tasks.models import (
    RecurringTaskTemplate, Task, TaskNote,
    Claim, Work, WorkNote, Nag,
    Worker, UnavailableDates, Snippet,
    TimeAccountEntry, Play,
    Class, ClassPayment, Class_x_Person
)
from tasks.templatetags.tasks_extras import duration_str2
from books.admin import Sellable, Invoiceable, sale_link


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class NoteInline(admin.StackedInline):

    fields = ['author', 'content']

    readonly_fields = ['author']

    extra = 0

    class Meta:
        abstract = True

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def get_DayOfWeekListFilter_class(date_field_name):

    class DayOfWeekListFilter(admin.SimpleListFilter):
        title = date_field_name.replace("_", " ")
        parameter_name = 'day of week'

        def lookups(self, request, model_admin):
            return (
                ('Mon', _('Monday')),
                ('Tue', _('Tuesday')),
                ('Wed', _('Wednesday')),
                ('Thu', _('Thursday')),
                ('Fri', _('Friday')),
                ('Sat', _('Saturday')),
                ('Sun', _('Sunday')),
            )

        def queryset(self, request, queryset):
            if self.value() == 'Mon':
                return queryset.filter(**{"{}__week_day".format(date_field_name): 2})
            if self.value() == 'Tue':
                return queryset.filter(**{"{}__week_day".format(date_field_name): 3})
            if self.value() == 'Wed':
                return queryset.filter(**{"{}__week_day".format(date_field_name): 4})
            if self.value() == 'Thu':
                return queryset.filter(**{"{}__week_day".format(date_field_name): 5})
            if self.value() == 'Fri':
                return queryset.filter(**{"{}__week_day".format(date_field_name): 6})
            if self.value() == 'Sat':
                return queryset.filter(**{"{}__week_day".format(date_field_name): 7})
            if self.value() == 'Sun':
                return queryset.filter(**{"{}__week_day".format(date_field_name): 1})

    return DayOfWeekListFilter


class DayOfWeekListFilterForTemplates(admin.SimpleListFilter):
    title = "Day of Week"
    parameter_name = 'day of week'

    def lookups(self, request, model_admin):
        return (
            ('Mon', _('Monday')),
            ('Tue', _('Tuesday')),
            ('Wed', _('Wednesday')),
            ('Thu', _('Thursday')),
            ('Fri', _('Friday')),
            ('Sat', _('Saturday')),
            ('Sun', _('Sunday')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Mon':
            return queryset.filter(monday=True)
        elif self.value() == 'Tue':
            return queryset.filter(tuesday=True)
        elif self.value() == 'Wed':
            return queryset.filter(wednesday=True)
        elif self.value() == 'Thu':
            return queryset.filter(thursday=True)
        elif self.value() == 'Fri':
            return queryset.filter(friday=True)
        elif self.value() == 'Sat':
            return queryset.filter(saturday=True)
        elif self.value() == 'Sun':
            return queryset.filter(sunday=True)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def duration_fmt(dur: datetime.timedelta):
    if dur is None:
        return
    return duration_str2(dur)


duration_fmt.short_description = "Duration"


def time_window_fmt(start:datetime.time, dur:datetime.timedelta):
    if start is None or dur is None: return "Anytime"
    finish = nptime.from_time(start) + dur
    fmt = "%-H%M"
    return "%s to %s" % (start.strftime(fmt), finish.strftime(fmt))


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# These work for Task and RecurringTaskTemplate because
# Task.PRIO_<X> == RecurringTaskTemplate.PRIO_<X> for all defined X.

def set_priority(query_set, setting):
    for obj in query_set:
        obj.priority = setting
        obj.save()


def set_priority_low(model_admin, request, query_set):
    set_priority(query_set, Task.PRIO_LOW)


def set_priority_med(model_admin, request, query_set):
    set_priority(query_set, Task.PRIO_MED)


def set_priority_high(model_admin, request, query_set):
    set_priority(query_set, Task.PRIO_HIGH)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def set_active(query_set, setting):
    for obj in query_set:
        obj.active = setting
        obj.save()


def set_active_off(model_admin, request, query_set):
    set_active(query_set, False)


def set_active_on(model_admin, request, query_set):
    set_active(query_set, True)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def set_nag(query_set, setting):
    for obj in query_set:
        obj.should_nag = setting
        obj.save()


def set_nag_off(model_admin, request, query_set):
    set_nag(query_set, False)


def set_nag_on(model_admin, request, query_set):
    set_nag(query_set, True)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def set_nag_for_instances(query_set, setting):
    for template in query_set:
        set_nag(template.instances.all(), setting)


def set_nag_off_for_instances(model_admin, request, query_set):
    set_nag_for_instances(query_set, False)


def set_nag_on_for_instances(model_admin, request, query_set):
    set_nag_for_instances(query_set, True)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def update_future_instances(model_admin, request, query_set):
    for template in query_set:
        for task in template.instances.filter(scheduled_date__gte=datetime.date.today()):
            task.resync_with_template()


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Base classes for both Template and Task

class TemplateAndTaskBase(VersionAdmin):

    # Following is defined only to rename column:
    def anybody_is_eligible_fmt(self, obj: Task) -> bool:
        return obj.anybody_is_eligible
    anybody_is_eligible_fmt.boolean=True
    anybody_is_eligible_fmt.short_description = "Anybody"

    # Following is defined only to rename column:
    def should_nag_fmt(self, obj: Task) -> bool:
        return obj.should_nag
    should_nag_fmt.boolean=True
    should_nag_fmt.short_description = "Nag"

    def time_window_fmt(self, obj):
        return time_window_fmt(obj.work_start_time, obj.work_duration)
    time_window_fmt.short_description = "Time"

    def work_and_workers_fmt(self, obj):
        dur_str = duration_fmt(obj.max_work)
        ppl_str = "ppl" if obj.max_workers > 1 else "pers"
        return "%s for %d %s" % (dur_str, obj.max_workers, ppl_str)
    work_and_workers_fmt.short_description = "Amount of Work"

    def priority_fmt(self, obj): return obj.priority
    priority_fmt.short_description = "Prio"

    class Meta:
        abstract = True


class EligibleClaimant_Inline(admin.TabularInline):

    def allows_nags(self, obj) -> bool:
        return obj.member.worker.should_nag
    allows_nags.boolean = True

    def edit_worker(self, obj) -> str:
        return format_html("<a href='/admin/tasks/worker/{}/'>{}</a>", obj.member.worker.id, obj.member.friendly_name)

    fields = ["member", "should_nag", "allows_nags", "edit_worker"]
    readonly_fields = ["allows_nags", "edit_worker"]
    raw_id_fields = ['member']
    extra = 0


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class EligibleClaimantForTemplate_Inline(EligibleClaimant_Inline):
    model = RecurringTaskTemplate.eligible_claimants_2.through
    model._meta.verbose_name = "Eligible Claimant"
    model._meta.verbose_name_plural = "Eligible Claimants"


class RecurringTaskTemplateAdmin(TemplateAndTaskBase):

    # save_as = True   There are complications w.r.t. Task instances.

    # Following overrides the empty changelist value. See http://stackoverflow.com/questions/28174881/
    # TODO: Why should it be here? It applies to all views.
    def __init__(self,*args,**kwargs):
        super(RecurringTaskTemplateAdmin, self).__init__(*args, **kwargs)
        main.EMPTY_CHANGELIST_VALUE = '-'

    list_filter = ['priority', 'active', 'should_nag', DayOfWeekListFilterForTemplates]

    list_display = [
        'short_desc', 'recurrence_str',
        'time_window_fmt', 'work_and_workers_fmt',
        'priority_fmt', 'default_claimant', 'anybody_is_eligible_fmt',
        'owner', 'reviewer', 'active', 'should_nag_fmt'
    ]
    actions = [
        update_future_instances,
        set_nag_on,
        set_nag_off,
        set_nag_on_for_instances,
        set_nag_off_for_instances,
        set_active_on,
        set_active_off,
        set_priority_low,
        set_priority_med,
        set_priority_high,
    ]
    search_fields = [
        'short_desc',
        '^owner__auth_user__first_name',
        '^owner__auth_user__last_name',
        '^owner__auth_user__username',
        '^default_claimant__auth_user__first_name',
        '^default_claimant__auth_user__last_name',
        '^default_claimant__auth_user__username',
        # TODO: Add eligibles, claimants, etc, here?
    ]

    inlines = [
        EligibleClaimantForTemplate_Inline,
    ]

    raw_id_fields = ['owner', 'default_claimant', 'reviewer']
    fieldsets = [

        (None, {'fields': [
            'short_desc',
            'instructions',
            'start_date',
            'priority',
            'active',
            'should_nag',
        ]}),

        ("Work Window", {
            'description': "If the work must be performed at a certain time, specify the start time and duration here.<br/>If the work can be done at any time, don't specify anything here.",
            'fields': [
                'work_start_time',
                'work_duration',
            ],
        }),

        ("Amount of Work", {
            'description': "Example 1: If 4 members will meet to work on a task from noon until 1pm, you want something like max_workers=4 and max_work=4 hours.<br/><br/>Example 2: If you have about 20 hours of electrical work that can be done anytime, then max_work=20 and max_workers would be whatever you think is sensible.",
            'fields': [
                'max_workers',
                'max_work'
            ],
        }),

        ("People", {'fields': [
            'owner',
            'anybody_is_eligible',
            'default_claimant',
            'reviewer',
        ]}),
        ("Recur by Day-of-Week and Position-in-Month", {
            'description': "Use this option for schedules like '1st and 3rd Thursday.'",
            'fields': [
                (
                    'first',
                    'second',
                    'third',
                    'fourth',
                    'last',
                    'every',
                ),
                (
                    'monday',
                    'tuesday',
                    'wednesday',
                    'thursday',
                    'friday',
                    'saturday',
                    'sunday',
                ),
                (
                    'jan',
                    'feb',
                    'mar',
                    'apr',
                    'may',
                    'jun',
                    'jul',
                    'aug',
                    'sep',
                    'oct',
                    'nov',
                    'dec',
                )
            ]
        }),

        ("Recur every X Days", {
            'description': "Use this option for schedules like 'Every 90 days'",
            'fields': [
                'repeat_interval',
                'missed_date_action',
            ]
        }),

    ]

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


# TODO: Can't use @admin.register decorator for RTTA because of main.EMPTY_CHANGELIST_VALUE = '-' code.
admin.site.register(RecurringTaskTemplate, RecurringTaskTemplateAdmin)


class TaskNoteInline(admin.StackedInline):
    raw_id_fields = ['author']
    model = TaskNote
    extra = 0


class WorkInline(admin.TabularInline):
    raw_id_fields = ['witness']
    model = Work
    extra = 0


class ClaimInline(admin.TabularInline):
    raw_id_fields = ['claiming_member']
    model = Claim
    extra = 0


def get_ScheduledDateListFilter_class(date_field_name):

    class ScheduledDateListFilter(admin.SimpleListFilter):
        title = date_field_name.replace("_", " ")
        parameter_name = 'direction'

        def lookups(self, request, model_admin):
            return (
                ('past', _('In the past')),
                ('today', _('Today')),
                ('future', _('In the future')),
                ('nodate', _('No date')),
            )

        def queryset(self, request, queryset):
            if self.value() == 'past':
                return queryset.filter(**{"%s__lt" % date_field_name: datetime.date.today()})
            if self.value() == 'today':
                return queryset.filter(**{"%s" % date_field_name: datetime.date.today()})
            if self.value() == 'future':
                return queryset.filter(**{"%s__gt" % date_field_name: datetime.date.today()})
            if self.value() == 'nodate':
                return queryset.filter(**{"%s__isnull" % date_field_name: True})

    return ScheduledDateListFilter


class EligibleClaimantForTask_Inline(EligibleClaimant_Inline):
    model = Task.eligible_claimants_2.through
    model._meta.verbose_name = "Eligible Claimant"
    model._meta.verbose_name_plural = "Eligible Claimants"


@admin.register(Task)
class TaskAdmin(TemplateAndTaskBase):

    # Following is defined only to rename column:
    def scheduled_date_fmt(self, obj: Task) -> datetime.date:
        return obj.scheduled_date
    scheduled_date_fmt.short_description = "Scheduled"

    actions = [
        set_nag_on,
        set_nag_off,
        set_priority_low,
        set_priority_med,
        set_priority_high,
    ]
    list_display = [
        'pk', 'short_desc', 'scheduled_weekday', 'scheduled_date_fmt',
        'time_window_fmt', 'anybody_is_eligible_fmt', 'work_and_workers_fmt',
        'priority_fmt', 'owner', 'should_nag_fmt', 'reviewer', 'status',
    ]
    search_fields = [
        'short_desc',
        '^owner__auth_user__first_name',
        '^owner__auth_user__last_name',
        '^owner__auth_user__username',
        # TODO: Add eligibles, claimants, etc, here?
    ]
    list_filter = [
        get_ScheduledDateListFilter_class('scheduled_date'),
        get_DayOfWeekListFilter_class('scheduled_date'),
        'priority',
        'status',
        'should_nag',
        'anybody_is_eligible'
    ]
    date_hierarchy = 'scheduled_date'
    fieldsets = [

        (None, {'fields': [
            'short_desc',
            'instructions',
        ]}),

        ("When", {'fields': [
            'scheduled_date',
            'work_start_time',
            'work_duration',
            'deadline',
        ]}),

        ("How Much", {'fields': [
            'max_work',
            'max_workers',
        ]}),

        ("People", {'fields': [
            'owner',
            'anybody_is_eligible',
            'reviewer',
        ]}),

        ("Completion", {
            'fields': [
                'should_nag',
                'status',
            ]
        }),
    ]
    inlines = [
        ClaimInline,
        EligibleClaimantForTask_Inline,
        TaskNoteInline,
    ]
    raw_id_fields = ['owner', 'eligible_claimants_2', 'reviewer']

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):  # No need to version these

    list_display = ['pk', 'claimed_task', 'claiming_member', 'claimed_start_time', 'claimed_duration', 'stake_date', 'status']
    list_filter = ['status']
    inlines = [WorkInline]
    search_fields = [
        '^claiming_member__auth_user__first_name',
        '^claiming_member__auth_user__last_name',
        '^claiming_member__auth_user__username',
        'claimed_task__short_desc',
    ]
    list_display_links = ['pk', 'claiming_member']  # Temporary measure to ease Work Trade data entry.
    fieldsets = [

        (None, {
            'fields': [
                'claimed_task',
                'claiming_member',
                'claimed_start_time',
                'claimed_duration',
            ]
        }),

        ("Status", {
            'fields': [
                'status',
                'date_verified',
            ]
        }),
    ]
    raw_id_fields = ['claimed_task', 'claiming_member']

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Wojciech's term.
        }


@admin.register(Nag)
class NagAdmin(admin.ModelAdmin):  # No need to version these

    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = "#tasks"

    def claim_count(self, obj):
        return obj.claims.count()
    claim_count.short_description = "#claims"

    list_display = ['pk', 'who', 'task_count', 'claim_count', 'when', 'auth_token_md5']

    readonly_fields = ['who', 'auth_token_md5', 'tasks', 'claims']

    fields = ['who', 'auth_token_md5', 'claims', 'tasks']

    search_fields = [
        '^who__auth_user__first_name',
        '^who__auth_user__last_name',
        '^who__auth_user__username',
    ]


class WorkNoteInline(NoteInline):
    model = WorkNote


@admin.register(Work)
class WorkAdmin(VersionAdmin):
    raw_id_fields = ['claim', 'witness']
    list_display = ['pk', 'claim', 'work_date', 'work_start_time', 'work_duration', 'witness']
    list_filter = [get_ScheduledDateListFilter_class('work_date')]
    date_hierarchy = 'work_date'
    search_fields = [
        '^claim__claiming_member__auth_user__first_name',
        '^claim__claiming_member__auth_user__last_name',
        '^claim__claiming_member__auth_user__username',
        'claim__claimed_task__short_desc',
    ]
    inlines = [WorkNoteInline]


# REVIEW: Following class is very similar to MemberTypeFilter. Can they be combined?
class WorkerTypeFilter(admin.SimpleListFilter):
    title = "Worker Type"
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return (
            ('worktrade', _('Work-Trader')),
            ('intern', _('Intern')),
            ('scholar', _('Scholarship')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'worktrade': return queryset.filter(member__tags__name="Work-Trader")
        if self.value() == 'intern':    return queryset.filter(member__tags__name="Intern")
        if self.value() == 'scholar':   return queryset.filter(member__tags__name="Scholarship")


class UnavailableDates_Inline(admin.TabularInline):
    model = UnavailableDates
    extra = 0


@admin.register(Worker)
class WorkerAdmin(VersionAdmin):

    def alarm(self, obj): return obj.should_include_alarms
    def nag(self, obj): return obj.should_nag
    def wmtd(self, obj): return obj.should_report_work_mtd
    alarm.boolean = True
    nag.boolean = True
    wmtd.boolean = True

    list_display = [
        'pk',
        'member',
        'alarm', 'nag', 'wmtd',
        # 'should_include_alarms', 'should_nag', 'should_report_work_mtd',
        'calendar_token',
    ]

    list_display_links = ['pk', 'member']

    list_filter = [WorkerTypeFilter, 'should_include_alarms', 'should_nag', 'should_report_work_mtd']

    raw_id_fields = ['member']

    search_fields = [
        '^member__auth_user__first_name',
        '^member__auth_user__last_name',
        '^member__auth_user__username',
    ]
    inlines = [UnavailableDates_Inline]


@admin.register(TaskNote)
class TaskNoteAdmin(VersionAdmin):
    list_display = ['pk', 'task', 'author', 'content']
    raw_id_fields = ['author']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Snippets

@admin.register(Snippet)
class SnippetAdmin(VersionAdmin):
    list_display = ['pk', 'name', 'description']
    search_fields = ['name', 'description', 'text']
    list_display_links = ['pk', 'name']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# TIME ACCOUNTS

@admin.register(TimeAccountEntry)
class TimeAccountEntryAdmin(VersionAdmin):

    def statement(self, obj): return obj.worker.should_report_work_mtd
    statement.boolean = True

    list_display = ['pk', 'worker', 'statement', 'when', 'type', 'change', 'explanation', 'expires']

    fields = ['worker', 'when', 'change', 'explanation', 'work', 'play', 'mship', 'balance']

    search_fields = [
        '^worker__member__auth_user__first_name',
        '^worker__member__auth_user__last_name',
        '^worker__member__auth_user__username',
        'worker__member__auth_user__email',
    ]

    ordering = ['when']
    date_hierarchy = 'when'

    raw_id_fields = ['worker', 'work', 'play', 'mship']

    readonly_fields = [
        'balance',  # Balances are automatically calculated.
    ]

    class NumTypeFilter(admin.SimpleListFilter):
        title = "Change"
        parameter_name = 'Sign'

        def lookups(self, request, model_admin):
            return (
                ('-', _('Negative')),
                ('0', _('Zero')),
                ('+', _('Positive')),
                ('N', _('Nonzero')),
            )

        def queryset(self, request, queryset):
            if self.value() == '-':
                return queryset.filter(change__lt=Decimal("0.00"))
            elif self.value() == '0':
                return queryset.filter(change=Decimal("0.00"))
            elif self.value() == '+':
                return queryset.filter(change__gt=Decimal("0.00"))
            elif self.value() == 'N':
                return queryset.exclude(change=Decimal("0.00"))

    list_filter = [NumTypeFilter, 'type']

    class Media:
        css = {
            "all": ("tasks/time-account-admin.css",)  # This hides "denormalized object descs", to use Woj's term.
        }


@admin.register(Play)
class PlayAdmin(VersionAdmin):
    raw_id_fields = ['playing_member']
    list_display = ['pk', 'play_date', 'playing_member', 'play_start_time', 'play_duration']
    list_filter = [get_ScheduledDateListFilter_class('play_date')]
    date_hierarchy = 'play_date'
    search_fields = [
        '^playing_member__auth_user__first_name',
        '^playing_member__auth_user__last_name',
        '^playing_member__auth_user__username',
    ]


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CLASSES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(Class)
class ClassAdmin(VersionAdmin):

    class InterestedPerson_Inline(admin.TabularInline):

        # This method is only needed to tag the field as boolean.
        def paid(self, obj:Class_x_Person) -> bool:
            return obj.paid
        paid.boolean = True

        model = Class_x_Person
        model._meta.verbose_name = "Interested Person"
        model._meta.verbose_name_plural = "Interested People"
        fields = ["the_person", "status", 'paid']
        raw_id_fields = ['the_person']
        readonly_fields = ['paid']
        extra = 0

    fields = [
        ('scheduled_date', 'start_time', 'canceled'),
        ('title', 'short_desc'),
        'info',
        ('max_students', 'minor_policy'),
        'department',
        'teaching_task',
        ('member_price', 'nonmember_price', 'materials_fee'),
        ('prerequisite_tag', 'certification_tag'),
        ('publicity_image', 'printed_handout'),
    ]

    readonly_fields = ['scheduled_date', 'start_time']

    inlines = [InterestedPerson_Inline]

    raw_id_fields = ['teaching_task']
    class Media:
        css = {
            "all": (
                "abutils/admin-tabular-inline.css", # This hides "denormalized object descs", to use Wojciech's term.
                "tasks/class-admin.css"
            )
        }


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Line-Item Inlines for SaleAdmin in Books app.
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@Sellable(ClassPayment)
class ClassPaymentLineItem(admin.StackedInline):
    extra = 0
    fields = [
        'the_class',
        'the_person',
        'sale_price',
        'financial_aid_discount',
    ]
    raw_id_fields = ['the_person', 'the_class',]

