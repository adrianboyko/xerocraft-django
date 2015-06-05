from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models
from .models import Member, Tag, RecurringTaskTemplate, Task, TaskNote

class MemberAdmin(admin.ModelAdmin):

    class Media:
        css = {
            "all": ("tasks/member_admin.css",)
        }

    filter_horizontal = ['tags']

class RecurringTaskTemplateAdmin(admin.ModelAdmin):

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
            'description': "Use this option for schedules like 'Every 1st and 3rd Thursday'",
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
    ]

admin.site.register(Member, MemberAdmin)
admin.site.register(RecurringTaskTemplate, RecurringTaskTemplateAdmin)

admin.site.register(Tag)
admin.site.register(Task)
admin.site.register(TaskNote)

