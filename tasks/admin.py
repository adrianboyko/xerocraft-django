from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models
from .models import Member, Tag, RecurringTaskTemplate, Task, TaskNote

class MemberAdmin(admin.ModelAdmin):

    list_display = ('first_name', 'last_name', 'user_id', 'active')
    class Media:
        css = {
            "all": ("tasks/member_admin.css",)
        }

    filter_horizontal = ['tags']

def create_create_tasks(number_of_days):
    def create_tasks(model_admin, request, query_set):
        for template in query_set:
            template.create_tasks(number_of_days)
    create_tasks.short_description = "Create tasks for next %d days" % number_of_days
    return create_tasks


class RecurringTaskTemplateAdmin(admin.ModelAdmin):

    list_display = ['short_desc','recurrence_str', 'owner', 'reviewer', 'suspended']
    actions = [create_create_tasks(60)]

    class Media:
        css = {
            "all": ("tasks/recurring_task_template_admin.css",)
        }

    filter_horizontal = ['eligible_claimants', 'eligible_tags']

    fieldsets = [

        (None, {'fields': [
            'short_desc',
            'instructions',
            'work_estimate',
            'start_date',
            'suspended',
        ]}),

        ("People", {'fields': [
            'owner',
            'eligible_claimants',
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
                'flexible_dates',
            ]
        }),

    ]

class TaskNoteInline(admin.StackedInline):
    model = TaskNote
    extra = 0

class TaskAdmin(admin.ModelAdmin):

    class Media:
        css = {
            "all": ("tasks/task_admin.css",)
        }

    filter_horizontal = ['eligible_claimants', 'eligible_tags']
    list_display = ['short_desc', 'scheduled_weekday', 'scheduled_date', 'owner', 'claimed_by', 'work_done', 'reviewer', 'work_accepted']

    fieldsets = [

        (None, {'fields': [
            'short_desc',
            'instructions',
            'work_estimate',
            'scheduled_date',
            'deadline',
        ]}),

        ("People", {'fields': [
            'owner',
            ('claimed_by', 'claim_date', 'prev_claimed_by'),
            'eligible_claimants',
            'eligible_tags',
            'reviewer',
        ]}),

        ("Completion", {
            'fields': [
                'work_done',
                'work_actual',
                'work_accepted',
            ]
        }),
    ]
    inlines = [TaskNoteInline]


admin.site.register(Member, MemberAdmin)
admin.site.register(RecurringTaskTemplate, RecurringTaskTemplateAdmin)
admin.site.register(Task, TaskAdmin)

admin.site.register(Tag)

