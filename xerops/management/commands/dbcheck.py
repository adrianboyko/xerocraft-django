
# Standard

import unittest
import sys

# Third Party
from django.core.management.base import BaseCommand
from django.apps import apps
from django.core.exceptions import ValidationError

# Local


__author__ = 'adrian'


class Command(BaseCommand):

    help = "Runs validation for each model in the database."

    def handle(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(DbCheck)
        unittest.TextTestRunner().run(suite)


class DbCheck(unittest.TestCase):

    def test_models(self):

        total_err_count = 0
        problems = []

        #TODO: Get list of apps from settings module.
        for appname in ['books', 'inventory', 'members', 'modelmailer', 'tasks', 'xerops', 'xis']:
            print(appname)
            app = apps.get_app_config(appname)
            for modelname, model in app.models.items():
                total_obj_count = model.objects.count()
                model_info_str = "   {}, {} objs".format(modelname, total_obj_count)
                print(model_info_str, end="")
                sys.stdout.flush()
                obj_count = 0
                model_err_count = 0
                errstr = ""
                for obj in model.objects.all():  # TODO: Call model.objs_for_dbcheck() instead, if it exists.
                    # if type(obj).__name__ != "JournalEntry": continue
                    try:
                        obj.full_clean()
                        if hasattr(obj, "dbcheck"): obj.dbcheck()
                    except ValidationError as e:
                        problems.append("{} #{}, {} {}".format(modelname, obj.pk, obj, e.messages))
                        model_err_count += 1
                        total_err_count += 1
                        continue
                    finally:
                        obj_count += 1
                        if obj_count % 10 == 0:
                            progress = obj_count/total_obj_count
                            errstr = ", *** {} ERRS ***".format(model_err_count) if model_err_count > 0 else ""
                            print("\r{}, {:.0%} done{}".format(model_info_str, progress, errstr), end="")
                            sys.stdout.flush()
                print("\r{}{}".format(model_info_str, errstr), end="")
                # Above string is shorter than the string it replaces. So print some spaces to clear out leftover:
                print("                     ")

        if total_err_count > 0:
            print("DBCheck found the following issues:")
            for problem in problems:
                print("   "+problem)
            sys.stdout.flush()
