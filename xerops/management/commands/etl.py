from django.core.management.base import BaseCommand, CommandError

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Meant to be run on a server other than the web server, this ETLs financials from various sources."

    auth_headers = None

    def handle(self, *args, **options):

        print("")
        fetchers = input("Fetchers: ").split()
        # fetchers = ["xerops.etlfetchers.paypal"]
        rest_token = input("REST API token: ")

        fetchers = [__import__(x, fromlist=["Fetcher"]) for x in fetchers]
        fetchers = [getattr(x, 'Fetcher') for x in fetchers]
        fetchers = [x() for x in fetchers]

        for fetcher in fetchers:
            if fetcher.skip:
                print("\nSkipping {}".format(str(fetcher)))
            else:
                print("\nProcessing {}".format(str(fetcher)))
                fetcher.django_auth_headers = {'Authorization': "Token " + rest_token}
                fetcher.fetch()