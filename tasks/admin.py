from django.contrib import admin
from django.contrib.admin.views import main
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from tasks.models import RecurringTaskTemplate, Task, TaskNote, Claim, Work, Nag, CalendarSettings


def duration_fmt(dur):
    if dur is None: return
    from tasks.templatetags.tasks_extras import duration_str
    return duration_str(dur)
duration_fmt.short_description = "Duration"


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
class RecurringTaskTemplateAdmin(admin.ModelAdmin):

    def duration_fmt(self, obj): return duration_fmt(obj.duration)
    duration_fmt.short_description = "Duration"

    save_as = True

    # Following overrides the empty changelist value. See http://stackoverflow.com/questions/28174881/
    def __init__(self,*args,**kwargs):
        super(RecurringTaskTemplateAdmin, self).__init__(*args, **kwargs)
        main.EMPTY_CHANGELIST_VALUE = '-'

    list_filter = ['active','should_nag']
    list_display = ['short_desc','recurrence_str', 'start_time', 'duration_fmt', 'owner', 'reviewer', 'active', 'should_nag']
    actions = [
        set_nag_on,
        set_nag_off,
        set_nag_on_for_instances,
        set_nag_off_for_instances,
        set_active_on,
        set_active_off,
    ]
    search_fields = [
        'short_desc',
        'owner__auth_user__first_name',
        'owner__auth_user__last_name',
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
            'work_estimate',
            'start_date',
            'start_time',
            'duration',
            'active',
            'should_nag',
        ]}),

        ("People", {'fields': [
            'owner',
            'max_claimants',
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


class TaskNoteInline(admin.StackedInline):
    model = TaskNote
    extra = 0


class ClaimInline(admin.StackedInline):
    model = Claim
    extra = 0


class WorkInline(admin.StackedInline):
    model = Work
    extra = 0


class TaskAdmin(admin.ModelAdmin):

    class Media:
        css = {
            "all": ("tasks/task_admin.css",)
        }

    def duration_fmt(self, obj): return duration_fmt(obj.duration)
    duration_fmt.short_description = "Duration"

    actions = [set_nag_on, set_nag_off]
    filter_horizontal = ['eligible_claimants', 'eligible_tags']
    list_display = ['pk', 'short_desc', 'scheduled_weekday', 'scheduled_date', 'start_time', 'duration_fmt', 'owner', 'should_nag', 'work_done', 'reviewer', 'work_accepted']
    search_fields = ['short_desc', 'owner__auth_user__first_name', 'owner__auth_user__last_name']
    list_filter = ['scheduled_date', 'work_done',]
    date_hierarchy = 'scheduled_date'
    fieldsets = [

        (None, {'fields': [
            'short_desc',
            'instructions',
            'work_estimate',
            'scheduled_date',
            'duration',
            'deadline',
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
                'work_done',
                'work_accepted',
            ]
        }),
    ]
    inlines = [TaskNoteInline, ClaimInline, WorkInline]


class ClaimAdmin(admin.ModelAdmin):

    list_display = ['pk', 'task', 'member', 'hours_claimed', 'date', 'status']
    list_filter = ['status']
    search_fields = [
        'member__auth_user__first_name',
        'member__auth_user__last_name',
        'task__short_desc',
    ]


class NagAdmin(admin.ModelAdmin):
    list_display = ['pk', 'who', 'task_count', 'when', 'auth_token_md5']
    readonly_fields = ['who','auth_token_md5','tasks']


class CalendarSettingsAdmin(admin.ModelAdmin):
    list_display = ['pk', 'who', 'token', 'include_alarms',]

admin.site.register(RecurringTaskTemplate, RecurringTaskTemplateAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Claim, ClaimAdmin)
admin.site.register(Nag, NagAdmin)
admin.site.register(CalendarSettings, CalendarSettingsAdmin)