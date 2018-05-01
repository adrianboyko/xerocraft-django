
# Standard

import unittest
import sys
import multiprocessing as mp
from typing import List, Optional

# Third Party
from django.core.management.base import BaseCommand
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connection

# Local


__author__ = 'adrian'
NUM_CORE = 4


class Command(BaseCommand):

    help = "Runs validation for each model in the database."

    def handle(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(DbCheck)
        unittest.TextTestRunner().run(suite)


def test_object(modelname_and_obj) -> List[str]:
    modelname, obj = modelname_and_obj
    #if type(obj).__name__ != "JournalEntry": return []
    try:
        obj.full_clean()
        if hasattr(obj, "dbcheck"): obj.dbcheck()
        return []
    except ValidationError as e:
        return ["{} #{}, {} {}".format(modelname, obj.pk, obj, e.messages)]


class DbCheck(unittest.TestCase):

    def test_models(self):
        problems = []
        total_err_count = 0

        connection.close()
        pool = mp.Pool(NUM_CORE)

        # TODO: Get list of apps from settings module.
        for appname in ['books', 'inventory', 'members', 'modelmailer', 'soda', 'tasks', 'bzw_ops', 'xis']:
            print(appname)
            app = apps.get_app_config(appname)
            for modelname, model in app.models.items():
                total_obj_count = model.objects.count()
                model_info_str = "   {}, {} objs".format(modelname, total_obj_count)
                print(model_info_str, end="")
                sys.stdout.flush()
                objs = model.objects.all()  # TODO: Call model.objs_for_dbcheck() instead, if it exists.
                model_problems = pool.map(
                    test_object,
                    ((modelname, obj) for obj in objs)
                )
                model_err_count = 0
                for obj_problems in model_problems:
                    problems.extend(obj_problems)
                    total_err_count += len(obj_problems)
                    model_err_count += len(obj_problems)

                print(", {} problems".format(model_err_count))

        if total_err_count > 0:
            print("DBCheck found the following issues:")
            for problem in problems:
                print("   "+problem)
            sys.stdout.flush()
