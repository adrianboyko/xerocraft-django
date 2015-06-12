from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Member, Tag, RecurringTaskTemplate, Task, TaskNote

class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'member'

class UserAdmin(UserAdmin):

    inlines = (MemberInline,)

    # list_display = ('first_name', 'user.last_name', 'main_web_id', 'user.active')

    # class Media:
    #     css = {
    #         "all": ("tasks/member_admin.css",)
    #     }

    # filter_horizontal = ['tags']

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

def create_create_tasks(number_of_days):
    """ Return an admin action function that creates tasks up to a certain number of days into the future.
    :param number_of_days: How far forward the desired function should schedule tasks
    :return: a function that schedules tasks
    """
    def create_tasks(model_admin, request, query_set):
        """ See admin action documentation. """
        """ TODO: If there are foreseeable error conditions that may occur while running your action, you
        should gracefully inform the user of the problem. This means handling exceptions and using
        django.contrib.admin.ModelAdmin.message_user() to display a user friendly description of the problem
        in the response.
        """
        for template in query_set:
            template.create_tasks(number_of_days)
    create_tasks.short_description = "Create tasks for next %d days" % number_of_days
    return create_tasks


class RecurringTaskTemplateAdmin(admin.ModelAdmin):

    list_display = ['short_desc','recurrence_str', 'owner', 'reviewer', 'active']
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

admin.site.register(RecurringTaskTemplate, RecurringTaskTemplateAdmin)
admin.site.register(Task, TaskAdmin)

admin.site.register(Tag)

