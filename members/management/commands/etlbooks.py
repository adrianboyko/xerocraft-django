from django.core.management.base import BaseCommand, CommandError
from members.models import PaidMembership
from . fetchers import TwoCheckoutFetcher, WePayFetcher, SquareFetcher
from members.serializers import PaidMembershipSerializer
import requests
import logging
import sys

__author__ = 'adrian'


def is_subset_dict(larger, smaller):
    for key, value in smaller.items():
        if not key in larger: return False
        elif larger[key] != smaller[key]: return False
    return True


class Command(BaseCommand):

    help = "Meant to be run on a server other than the web server, this ETLs financials from various sources."

    URL = "http://xerocraft-django.herokuapp.com/members/paidmemberships/"  # IMPORTANT: Set URL back to production
    #URL = "http://localhost:8000/members/paidmemberships/"

    auth_headers = None

    def handle_fetcher(self, fetcher):

        session = requests.Session()
        progcount = 0

        print("")
        for pm in fetcher.generate_paid_memberships():

            # See if the PaidMembership has previously been sent:
            get_params = {'payment_method': pm.payment_method, 'ctrlid': pm.ctrlid}
            response = session.get(self.URL, params=get_params, headers=self.auth_headers)
            matchcount = int(response.json()['count'])
            if matchcount == 0:
                id = None
            elif matchcount == 1:
                djangodata = response.json()['results'][0]
                id = int(djangodata['id'])
            else:
                # Else case is an assertion that matchcount is 0 or 1.
                raise AssertionError("Too many matches for method %s ctrlid %s" % (pm.payment_method, pm.ctrlid))

            # Either POST or PUT depending on whether it already exists
            fetched_data = PaidMembershipSerializer(pm).data
            if id is None:
                # The information is not yet on the website, so add it.
                response = session.post(self.URL, fetched_data, headers=self.auth_headers)
                progchar = "+"  # Added
            else:
                fetched_data.update({'id': djangodata['id'], 'protected': False})  # So subset comparison can be made.
                if djangodata['protected']:
                    progchar = "P"  # Protected, so will leave it alone.
                elif is_subset_dict(djangodata, fetched_data):
                    progchar = "="  # Equal so no add or update required. Will leave it alone.
                else:
                    response = session.put("{}{}/".format(self.URL, id), fetched_data, headers=self.auth_headers)
                    progchar = "U"  # Change detected so updated.
            if response.status_code >= 300:
                progchar = "E"  # Error

            print(progchar, end='')  # Progress indicator
            progcount += 1
            if progcount % 50 == 0:
                print(" {}".format(progcount))
            sys.stdout.flush()
        if progcount % 50 != 0: print("")

    def handle(self, *args, **options):

        print("Will push data to {}".format(self.URL))
        rest_token = input("REST API token: ")
        self.auth_headers = {'Authorization': "Token " + rest_token}

        # TODO: THE LIST OF FETCHERS SHOULD COME FROM THE SETTINGS FILE.
        fetchers = [WePayFetcher(), SquareFetcher(), TwoCheckoutFetcher()]
        for fetcher in fetchers:
            self.handle_fetcher(fetcher)

        print("")