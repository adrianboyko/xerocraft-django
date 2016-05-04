from django.core.management.base import NoArgsCommand
from django.apps import apps
from django.core.exceptions import ValidationError
import unittest
import sys

__author__ = 'adrian'


class Command(NoArgsCommand):

    help = "Runs validation for each model in the database."

    def handle_noargs(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(DbCheck)
        unittest.TextTestRunner().run(suite)


class DbCheck(unittest.TestCase):

    def test_models(self):

        for appname in ['tasks', 'books', 'inventory', 'members', 'xerocraft']:
            print(appname)
            app = apps.get_app_config(appname)
            for modelname, model in app.models.items():
                print("   {} ({})".format(modelname, model.objects.count()))
                for obj in model.objects.all():
                    try:
                        obj.full_clean()
                        if hasattr(obj, "dbcheck") : obj.dbcheck()
                    except ValidationError as e:
                        print("      >>> {} {} {}".format(obj.pk, obj, e))
        sys.stdout.flush()
