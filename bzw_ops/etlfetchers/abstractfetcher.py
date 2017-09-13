# Standard
import abc
import sys

# Third Party
from django.db.models import Model
from rest_framework.test import APIRequestFactory
from requests import Session

# Local
import books.models as bm
import books.serializers as bs
import members.models as mm
import members.serializers as ms


def has_new_data(older, newer):
    for newkey, newval in newer.items():
        if newkey in ['id', 'protected']: continue
        if newval is None: continue
        if newkey not in older: return True
        elif older[newkey] != newer[newkey]: return True
    return False


class AbstractFetcher(object):

    __metaclass__ = abc.ABCMeta

    SERVERNAME = "xerocraft-django.herokuapp.com"
    URLBASE = "https://{}/".format(SERVERNAME)

    # SERVERNAME = "localhost:8000"  # IMPORTANT: Set URL back to production
    # URLBASE = "http://{}/".format(SERVERNAME)

    URLS = {
        bm.Sale:                        "books/sales/",
        bm.MonetaryDonation:            "books/monetary-donations/",
        bm.OtherItem:                   "books/other-items/",
        bm.OtherItemType:               "books/other-item-types/",
        mm.Membership:                  "members/api/memberships/",
        mm.MembershipGiftCardReference: "members/api/gift-card-refs/",
    }
    SERIALIZERS = {
        bm.Sale:                        bs.SaleSerializer,
        bm.MonetaryDonation:            bs.MonetaryDonationSerializer,
        bm.OtherItem:                   bs.OtherItemSerializer,
        mm.Membership:                  ms.MembershipSerializer,
        mm.MembershipGiftCardReference: ms.MembershipGiftCardReferenceSerializer,
    }

    CREDIT_CARD_NAME_MAP = {
        "VISA": "Visa",
        "MASTER_CARD": "MC",
        "MASTERCARD": "MC",
        "AMERICAN_EXPRESS": "Amex",
        "DISCOVER": "Disc"
    }

    djangosession = Session()

    progress_count = 0
    progress_per_row = 50

    django_auth_headers = None

    @abc.abstractmethod
    def fetch(self):
        """Extract, transform, and load data."""
        raise NotImplementedError("fetch() is not implemented")

    def _fetch_complete(self):
        if self.progress_count % self.progress_per_row != 0:
            print("")

    def _massage_sale(self, sale):
        if len(sale.payer_email) > 40:
            sale.payer_email = ""

    def upsert(self, item: Model) -> dict:

        if type(item) == bm.Sale: self._massage_sale(item)

        url = self.URLBASE + self.URLS[type(item)]
        serializer = self.SERIALIZERS[type(item)]

        # See if the item has previously been sent:
        get_params = {'ctrlid': item.ctrlid}
        response = self.djangosession.get(url, params=get_params, headers=self.django_auth_headers)
        if response.status_code >= 300:
            raise AssertionError("Unexpected status code from Django: "+str(response.status_code))
        matchcount = int(response.json()['count'])
        if matchcount == 0:
            id = None
        elif matchcount == 1:
            djangodata = response.json()['results'][0]
            id = int(djangodata['id'])
        else:
            # Else case is an assertion that matchcount is 0 or 1.
            raise AssertionError("Too many matches for %s with ctrlid %s" % (str(type(item)), item.ctrlid))

        # Creating srcdata is complicated by the fact that the API is now using HyperlinkedIdentityField
        # It requires a Django or DjangoRestFramework "Request" as context.
        # see http://stackoverflow.com/questions/10277748/how-to-get-request-object-in-django-unit-testing
        context = {'request':APIRequestFactory().get('/', SERVER_NAME=self.SERVERNAME, secure=True)}
        srcdata = serializer(item, context=context).data

        # Either POST or PUT depending on whether it already exists
        if id is None:
            # The information is not yet on the website, so add it.
            response = self.djangosession.post(url, srcdata, headers=self.django_auth_headers)
            djangodata = response.json()
            progchar = "+"  # Added
        else:
            #srcdata.update({'id': djangodata['id'], 'protected': False})  # So subset comparison can be made.
            if djangodata['protected']:
                progchar = "P"  # Protected, so will leave it alone.
            elif has_new_data(djangodata, srcdata):
                update_url = "{}{}/".format(url, id)
                response = self.djangosession.put(update_url, srcdata, headers=self.django_auth_headers)
                progchar = "U"  # Change detected so updated.
            else:
                progchar = "="  # Equal so no add or update required. Will leave it alone.
        if response.status_code >= 300:
            progchar = "E"  # Error

        print(progchar, end='')  # Progress indicator
        self.progress_count += 1
        if self.progress_count % self.progress_per_row == 0:
            print(" {}".format(self.progress_count))
        sys.stdout.flush()

        return djangodata

    def _get_id(self, url: str, filter: dict) -> dict:
        response = self.djangosession.get(self.URLBASE+url, params=filter, headers=self.django_auth_headers)
        if response.status_code >= 300:
            raise AssertionError("Unexpected status code from Django: "+str(response.status_code))
        matchcount = int(response.json()['count'])
        if matchcount == 0:
            id = None
        elif matchcount == 1:
            djangodata = response.json()['results'][0]
            id = int(djangodata['id'])
        else:
            # Else case is an assertion that matchcount is 0 or 1.
            raise AssertionError("Too many matches searching for {} with {}".format(url, filter))
        return id

    def card_type(self, number: str) -> str:
        if number is None: return None
        if number[:1] == "4": cardtype = "Visa"
        if int(number[:2]) >= 51 and int(number[:2]) <= 55: return "MC"
        if number[:2] == "34" or number[:2] == "37": return "Amex"
        if number[:4] == "6011": return "Disc"
        if number[:4] == "3528" or number[:4] == "3529": return "JCB"
        if int(number[:3]) >= 353 and int(number[:3]) <= 359: return "JCB"
        if number[:2] == "36": return "Dine"
        if int(number[:3]) >= 300 and int(number[:3]) <= 305: return "Dine"
