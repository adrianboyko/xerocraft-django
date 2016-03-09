import abc
from django.db.models import Model
import books.models as bm
import books.serializers as bs
import members.models as mm
import members.serializers as ms
from requests import Session
import sys


def is_subset_dict(larger, smaller):
    for key, value in smaller.items():
        if key in ['id', 'protected']: continue
        if not key in larger: return False
        elif larger[key] != smaller[key]: return False
    return True


class AbstractFetcher(object):

    __metalass__ = abc.ABCMeta

    #URLBASE = "http://xerocraft-django.herokuapp.com/"
    URLBASE = "http://localhost:8000/"  # IMPORTANT: Set URL back to production

    URLS = {
        bm.Sale:                        "books/sales/",
        bm.MonetaryDonation:            "books/monetary-donations/",
        mm.Membership:                  "members/memberships/",
        mm.MembershipGiftCardReference: "members/gift-card-refs/",
    }
    SERIALIZERS = {
        bm.Sale:                        bs.SaleSerializer,
        bm.MonetaryDonation:            bs.MonetaryDonationSerializer,
        mm.Membership:                  ms.MembershipSerializer,
        mm.MembershipGiftCardReference: ms.MembershipGiftCardReferenceSerializer,

    }

    djangosession = Session()

    progress_count = 0

    def __init__(self, django_auth_headers: dict):
        self.django_auth_headers = django_auth_headers

    @abc.abstractmethod
    def fetch(self):
        """Extract, transform, and load data."""
        raise NotImplementedError("fetch() is not implemented")

    def upsert(self, item: Model) -> dict:

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

        # Either POST or PUT depending on whether it already exists
        srcdata = serializer(item).data
        if id is None:
            # The information is not yet on the website, so add it.
            response = self.djangosession.post(url, srcdata, headers=self.django_auth_headers)
            djangodata = response.json()
            progchar = "+"  # Added
        else:
            #srcdata.update({'id': djangodata['id'], 'protected': False})  # So subset comparison can be made.
            if djangodata['protected']:
                progchar = "P"  # Protected, so will leave it alone.
            elif is_subset_dict(djangodata, srcdata):
                progchar = "="  # Equal so no add or update required. Will leave it alone.
            else:
                update_url = "{}{}/".format(url, id)
                response = self.djangosession.put(update_url, srcdata, headers=self.django_auth_headers)
                progchar = "U"  # Change detected so updated.
        if response.status_code >= 300:
            progchar = "E"  # Error

        print(progchar, end='')  # Progress indicator
        self.progress_count += 1
        if self.progress_count % 50 == 0:
            print(" {}".format(self.progress_count))
        sys.stdout.flush()

        return djangodata