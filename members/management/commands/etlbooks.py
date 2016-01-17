from django.core.management.base import BaseCommand, CommandError
from members.models import PaidMembership
from . fetchers import TwoCheckoutFetcher
from members.serializers import PaidMembershipSerializer
import requests
import logging
import lxml.html
import sys

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Meant to be run on a server other than the web server, this ETLs financials from various sources."

    def handle(self, *args, **options):

        session = requests.Session()
        dotcount = 0
        fetcher = TwoCheckoutFetcher()

        URL = "http://xerocraft-django.herokuapp.com/members/paidmemberships/"  # IMPORTANT: Set URL back to production
        #URL = "http://localhost:8000/members/paidmemberships/"

        print("Will push data to {}".format(URL))
        rest_token = input("REST API token: ")
        auth_headers = {'Authorization': "Token " + rest_token}

        for pm in fetcher.generate_payments():

            # See if the PaidMembership has previously been sent:
            get_params = {'payment_method': pm.payment_method, 'ctrlid': pm.ctrlid}
            response = session.get(URL, params=get_params, headers=auth_headers)
            matchcount = int(response.json()['count'])
            if matchcount == 0:
                id = None
            elif matchcount == 1:
                id = int(response.json()['results'][0]['id'])
            else:
                # Else case is an assertion that matchcount is 0 or 1.
                raise AssertionError("Too many matches for method %s ctrlid %s" % (pm.payment_method, pm.ctrlid))

            # Either POST or PUT depending on whether it already exists
            twocodata = PaidMembershipSerializer(pm).data
            if id is None:
                # The information is not yet on the website, so add it.
                response = session.post(URL, twocodata, headers=auth_headers)
                progchar = "+"  # Added
            else:
                # Are all the items from 2checkout already on the website?
                djangodata = response.json()['results'][0]
                if all(item in djangodata for item in twocodata):
                    # Yes, so don't do anything with the 2checkout data.
                    progchar = "I"  # Ignored
                else:
                    # No, so update the data on the website.
                    response = session.put("{}{}/".format(URL, id), twocodata, headers=auth_headers)
                    progchar = "U"  # Updated
            if response.status_code >= 300:
                progchar = "E"  # Error

            print(progchar, end='')
            dotcount += 1
            if dotcount % 50 == 0:
                print(" {}".format(dotcount))
            sys.stdout.flush()