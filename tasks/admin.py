from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models
from .models import Member, Tag, RecurringTaskTemplate, Task, TaskNote

class MemberAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple}
    }

admin.site.register(Member,MemberAdmin)
admin.site.register(Tag)
admin.site.register(RecurringTaskTemplate)
admin.site.register(Task)
admin.site.register(TaskNote)

