from django.core.management.base import BaseCommand, CommandError
from books.models import Sale, SaleNote
from members.models import Membership
from members.serializers import MembershipSerializer
import requests
import sys

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Meant to be run on a server other than the web server, this ETLs financials from various sources."

    auth_headers = None

    def handle(self, *args, **options):

        fetchers = input("Fetchers: ").split()
        rest_token = input("REST API token: ")


        django_auth_headers = {'Authorization': "Token " + rest_token}
        fetchers = [__import__(x, fromlist=["Fetcher"]) for x in fetchers]
        fetchers = [getattr(x, 'Fetcher') for x in fetchers]
        fetchers = [x(django_auth_headers) for x in fetchers]


        for fetcher in fetchers:
            fetcher.fetch()
            print("")
