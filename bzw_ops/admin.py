
# Standard

# Third Party
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Local
from bzw_ops.models import TimeBlockType, TimeBlock
from abutils.time import (
    days_of_week_str,
    duration_single_unit_str,
    ordinals_of_month_str,
)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class CustomUserAdmin(UserAdmin):
    def __init__(self, *args, **kwargs):
        super(UserAdmin,self).__init__(*args, **kwargs)
        new_list_display = list(UserAdmin.list_display)
        new_list_display.remove('is_staff')
        new_list_display = ['pk', 'is_active'] + new_list_display  # 'some_function'
        UserAdmin.list_display = new_list_display
        UserAdmin.list_display_links = ['username']

    # Function to count objects of each user from another Model (where user is FK)
    # def some_function(self, obj):
    #     return obj.another_model_set.count()


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):

    def fmt_ords_str(self, obj) -> str:
        return ordinals_of_month_str(obj)

    def fmt_days_str(self, obj) -> str:
        return days_of_week_str(obj)

    def fmt_dur_str(self, obj) -> str:
        return duration_single_unit_str(obj.duration)

    def fmt_types(self, obj) -> str:
        types = [bt.name for bt in obj.types.all()]
        return ", ".join(types)

    list_display = [
        'pk',
        'fmt_ords_str',
        'fmt_days_str',
        'start_time',
        'fmt_dur_str',
        'fmt_types'
    ]

    fields = [
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
        'start_time',
        'duration',
        'types',
    ]


TimeBlockAdmin.fmt_ords_str.short_description = "Ordinals"
TimeBlockAdmin.fmt_days_str.short_description = "Days"
TimeBlockAdmin.fmt_dur_str.short_description = "Duration"
TimeBlockAdmin.fmt_types.short_description = "Activities"


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@admin.register(TimeBlockType)
class TimeBlockTypeAdmin(admin.ModelAdmin):

    list_display = ['pk', 'name', 'is_default', 'description']
    list_display_links = ['pk', 'name']

