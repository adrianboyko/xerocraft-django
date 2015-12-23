from django.contrib import admin
from django.contrib.admin.views import main
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
import datetime
from tasks.models import RecurringTaskTemplate, Task, TaskNote, Claim, Work, Nag, Worker, WorkNote
from nptime import nptime
from tasks.templatetags.tasks_extras import duration_str2


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def duration_fmt(dur:datetime.timedelta):
    if dur is None: return
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

class TemplateAndTaskBase(admin.ModelAdmin):

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


class RecurringTaskTemplateAdmin(TemplateAndTaskBase):

    # save_as = True   There are complications w.r.t. Task instances.

    # Following overrides the empty changelist value. See http://stackoverflow.com/questions/28174881/
    # TODO: Why should it be here? It applies to all views.
    def __init__(self,*args,**kwargs):
        super(RecurringTaskTemplateAdmin, self).__init__(*args, **kwargs)
        main.EMPTY_CHANGELIST_VALUE = '-'

    list_filter = ['priority', 'active', 'should_nag']

    list_display = [
        'short_desc', 'recurrence_str',
        'time_window_fmt', 'work_and_workers_fmt',
        'priority_fmt', 'owner', 'reviewer', 'active', 'should_nag'
    ]
    actions = [
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
    ]

    class Media:
        css = {
            "all": ("tasks/recurring_task_template_admin.css",)
        }

    filter_horizontal = ['eligible_claimants', 'eligible_tags', 'uninterested']

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
            'default_claimant',
            'eligible_claimants',
            'uninterested',
            'eligible_tags',
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

# TODO: Can't use @admin.register decorator for RTTA because of main.EMPTY_CHANGELIST_VALUE = '-' code.
admin.site.register(RecurringTaskTemplate, RecurringTaskTemplateAdmin)


class TaskNoteInline(admin.StackedInline):
    model = TaskNote
    extra = 0


class WorkInline(admin.TabularInline):
    model = Work
    extra = 0


class ClaimInline(admin.StackedInline):
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


@admin.register(Task)
class TaskAdmin(TemplateAndTaskBase):

    class Media:
        css = {
            "all": ("tasks/task_admin.css",)
        }

    actions = [
        set_nag_on,
        set_nag_off,
        set_priority_low,
        set_priority_med,
        set_priority_high,
    ]
    filter_horizontal = ['eligible_claimants', 'eligible_tags']
    list_display = [
        'pk', 'short_desc', 'scheduled_weekday', 'scheduled_date',
        'time_window_fmt', 'work_and_workers_fmt',
        'priority_fmt', 'owner', 'should_nag', 'reviewer', 'status',
    ]
    search_fields = [
        'short_desc',
        '^owner__auth_user__first_name',
        '^owner__auth_user__last_name'
    ]
    list_filter = [get_ScheduledDateListFilter_class('scheduled_date'), 'priority', 'status']
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
            'eligible_claimants',
            'eligible_tags',
            'reviewer',
        ]}),

        ("Completion", {
            'fields': [
                'should_nag',
                'status',
            ]
        }),
    ]
    inlines = [TaskNoteInline, ClaimInline]


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):

    def temp_mtd_hours_rollup(self, obj):
        """This is a temporary measure to help audit work trade data entry. Will be moved to a new model, eventually. """
        if not obj.claimed_task.short_desc.startswith("Uncategorized"): return None
        today = datetime.date.today()
        mtd_seconds = 0
        for work in obj.work_set.all():
            workdate = work.work_date
            if workdate.year == today.year and workdate.month == today.month:
                mtd_seconds += work.work_duration.total_seconds()
        return "%.2f" % (mtd_seconds/3600.0)
    temp_mtd_hours_rollup.short_description = "WMTD"

    list_display = ['pk', 'claimed_task', 'temp_mtd_hours_rollup', 'claiming_member', 'claimed_start_time', 'claimed_duration', 'stake_date', 'status']
    list_filter = ['status']
    inlines = [WorkInline]
    search_fields = [
        '^claiming_member__auth_user__first_name',
        '^claiming_member__auth_user__last_name',
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


@admin.register(Nag)
class NagAdmin(admin.ModelAdmin):
    list_display = ['pk', 'who', 'task_count', 'when', 'auth_token_md5']
    readonly_fields = ['who','auth_token_md5','tasks']


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ['pk', 'claim', 'work_date', 'work_duration']
    list_filter = [get_ScheduledDateListFilter_class('work_date')]
    date_hierarchy = 'work_date'
    search_fields = [
        '^claim__claiming_member__auth_user__first_name',
        '^claim__claiming_member__auth_user__last_name',
        'claim__claimed_task__short_desc',
    ]


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


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):

    def alarm(self, obj): return obj.should_include_alarms
    def nag(self, obj): return obj.should_nag
    def wmtd(self, obj): return obj.should_report_work_mtd
    alarm.boolean = True
    nag.boolean = True
    wmtd.boolean = True

    def reported(self,obj):
        dur = obj.last_work_mtd_reported
        if dur == datetime.timedelta(0):
            return "-"
        else:
            return duration_fmt(obj.last_work_mtd_reported)

    list_display = [
        'pk',
        'member',
        'reported',
        'alarm', 'nag', 'wmtd',
        #'should_include_alarms', 'should_nag', 'should_report_work_mtd',
        'calendar_token',
    ]

    list_display_links = ['pk', 'member']

    list_filter = [WorkerTypeFilter]


@admin.register(TaskNote)
class TaskNoteAdmin(admin.ModelAdmin):
    list_display = ['pk', 'task', 'author', 'content']


@admin.register(WorkNote)
class WorkNoteAdmin(admin.ModelAdmin):
    list_display = ['pk', 'work', 'author', 'content']
