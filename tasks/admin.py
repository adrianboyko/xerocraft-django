from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models
from .models import Member, Tag, RecurringTaskTemplate, Task, TaskNote

class MemberAdmin(admin.ModelAdmin):

    class Media:
        css = {
            "all": ("tasks/member_admin.css",)
        }
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple}
    }

class RecurringTaskTemplateAdmin(admin.ModelAdmin):

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

        ("Recurrence Pattern", {'fields': [
            'first',
            'second',
            'third',
            'fourth',
            'last',
            'every',
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
        ]}),
    ]

admin.site.register(Member, MemberAdmin)
admin.site.register(RecurringTaskTemplate, RecurringTaskTemplateAdmin)

admin.site.register(Tag)
admin.site.register(Task)
admin.site.register(TaskNote)

