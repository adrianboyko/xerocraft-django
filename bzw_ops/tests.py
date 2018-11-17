
# Standard

# Third Party
from django.test import TestCase
from django.contrib import admin
from django.core.management import call_command

# Local

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

ADMIN_FIELDNAME_LISTS = [
    'fields',
    'exclude',
    'readonly_fields',
    'list_display',
    'list_display_links',
    'search_fields',
    'filter_horizontal',
    'filter_vertical',
    'list_filter',
    'raw_id_fields',
]

ADMIN_FIELDNAME_SINGLES = [
    'date_hierarchy',
]


# REVIEW: Is this test useful, anymore? Did Django add similar functionality, somewhere along the way?
class TestAdminConfig(TestCase):

    def test_admin_fieldname_lists(self):

        def check_fieldname(fieldname: str, model_class, admin_obj):
            if not isinstance(fieldname, str): return
            fieldname = fieldname.replace("^", "")
            # print("       field: %s" % fieldname)
            if fieldname in dir(model_class):
                return
            if fieldname in dir(admin_obj):
                return
            fieldname = fieldname.strip("=")
            model_class.objects.filter(**{fieldname: None})

        for model_class, admin_obj in admin.site._registry.items():

            # print("classes: %s, %s" % (model_class, admin_obj))

            # Check lists of field names
            for list_name in ADMIN_FIELDNAME_LISTS:
                list_of_fieldnames = getattr(admin_obj, list_name)
                if list_of_fieldnames is None:
                    continue
                # print("    list: %s" % list_name)
                for fieldname in list_of_fieldnames:
                    check_fieldname(fieldname, model_class, admin_obj)

            # Check individual field names
            for single_name in ADMIN_FIELDNAME_SINGLES:
                # print("    single: %s" % single_name)
                fieldname = getattr(admin_obj, single_name)
                check_fieldname(fieldname, model_class, admin_obj)

            # Check fieldsets, which is a special case.
            fieldsets = admin_obj.fieldsets
            if fieldsets is not None:
                for fieldset_name, field_options in fieldsets:
                    # print("    fieldset: %s" % fieldset_name)
                    fields = field_options["fields"]
                    for fieldname in fields:
                        check_fieldname(fieldname, model_class, admin_obj)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# class TestProductionDatabase(TestCase):
#
#     def test_with_dbcheck_command(self):
#         call_command('dbcheck')
