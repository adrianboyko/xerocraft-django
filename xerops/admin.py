

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class CustomUserAdmin(UserAdmin):
    def __init__(self, *args, **kwargs):
        super(UserAdmin,self).__init__(*args, **kwargs)
        new_list_display = list(UserAdmin.list_display)
        new_list_display.remove('is_staff')
        new_list_display = ['pk', 'is_active'] + new_list_display  # 'some_function'
        UserAdmin.list_display = new_list_display

    # Function to count objects of each user from another Model (where user is FK)
    # def some_function(self, obj):
    #     return obj.another_model_set.count()

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)