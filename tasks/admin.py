from django.contrib import admin
from django.contrib.admin.views import main
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from tasks.models import RecurringTaskTemplate, Task, TaskNote, Claim, Work, Nag


def toggle_should_nag(model_admin, request, query_set):
    for obj in query_set:
        assert type(obj) is Task or type(obj) is RecurringTaskTemplate
        obj.should_nag = not obj.should_nag
        obj.save()


def toggle_should_nag_for_instances(model_admin, request, query_set):
    for template in query_set:
        assert type(template) is RecurringTaskTemplate
        toggle_should_nag(model_admin, request, template.instances.all())


class RecurringTaskTemplateAdmin(admin.ModelAdmin):

    save_as = True

    # Following overrides the empty changelist value. See http://stackoverflow.com/questions/28174881/
    def __init__(self,*args,**kwargs):
        super(RecurringTaskTemplateAdmin, self).__init__(*args, **kwargs)
        main.EMPTY_CHANGELIST_VALUE = '-'

    list_display = ['short_desc','recurrence_str', 'start_time', 'duration', 'owner', 'reviewer', 'active', 'should_nag']
    actions = [toggle_should_nag, toggle_should_nag_for_instances]

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

    actions = [toggle_should_nag]
    filter_horizontal = ['eligible_claimants', 'eligible_tags']
    list_display = ['pk', 'short_desc', 'scheduled_weekday', 'scheduled_date', 'start_time', 'duration', 'owner', 'should_nag', 'work_done', 'reviewer', 'work_accepted']
    search_fields = ['short_desc', 'instructions']

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


class NagAdmin(admin.ModelAdmin):
    list_display = ['pk', 'who', 'task_count', 'when', 'auth_token_md5']
    readonly_fields = ['who','auth_token_md5','tasks']


admin.site.register(RecurringTaskTemplate, RecurringTaskTemplateAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Claim, ClaimAdmin)
admin.site.register(Nag, NagAdmin)
