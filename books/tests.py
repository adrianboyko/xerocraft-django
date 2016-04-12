from django.test import TestCase
from books.models import MonetaryDonation, Sale
from pydoc import locate  # for loading classes


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =]

class TestMonetaryDonation(TestCase):

    def test_monetarydonation_ctrlid_generation(self):
        sale = Sale.objects.create(total_paid_by_customer=100)
        mdon = MonetaryDonation.objects.create(sale=sale, amount=100)
        self.assertTrue(mdon.ctrlid.startswith("GEN"))

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =]

model_classnames = [
    "Account",
    "Donation",
    "ExpenseClaim",
    "ExpenseTransaction",
    "Donation",
    "OtherItemType",
    "Sale",
]

admin_fieldname_lists = [
    'fields',
    'exclude',
    'readonly_fields',
    'raw_fields',
    'list_display',
    'list_display_links',
    'search_fields',
    'filter_horizontal',
    'filter_vertical',
    'list_filter',
]

admin_fieldname_singles = [
    'date_hierarchy',
]


class TestAdminConfig(TestCase):

    def test_admin_fieldname_lists(self):

        def check_fieldname(fieldname, model_class, admin_class):
            if not isinstance(fieldname, str): return
            fieldname = fieldname.replace("^", "")
            print("       field: %s" % fieldname)
            if fieldname in dir(model_class): return
            if fieldname in dir(admin_class): return
            model_class.objects.filter(**{fieldname:None})

        for model_classname in model_classnames:
            model_class = locate("books.models.%s" % model_classname)
            admin_class = locate("books.admin.%sAdmin" % model_classname)
            print("classes: %s, %s" % (model_class.__name__, admin_class.__name__))

            # Check lists of field names
            for list_name in admin_fieldname_lists:
                list_of_fieldnames = getattr(admin_class, list_name)
                if list_of_fieldnames is None: continue
                print("    list: %s" % list_name)
                for fieldname in list_of_fieldnames:
                    check_fieldname(fieldname, model_class, admin_class)

            # Check individual field names
            for single_name in admin_fieldname_singles:
                print("    single: %s" % single_name)
                fieldname = getattr(admin_class, single_name)
                check_fieldname(fieldname, model_class, admin_class)

            # Check fieldsets, which is a special case.
            fieldsets = getattr(admin_class, 'fieldsets')
            if fieldsets is not None:
                for fieldset_name, field_options in fieldsets:
                    print("    fieldset: %s" % fieldset_name)
                    fields = field_options["fields"]
                    for fieldname in fields:
                        check_fieldname(fieldname, model_class, admin_class)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
