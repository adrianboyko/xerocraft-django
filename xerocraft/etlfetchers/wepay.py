
from xerocraft.etlfetchers.abstractfetcher import AbstractFetcher
from members.models import Membership
from books.models import Sale, SaleNote
from hashlib import md5
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import requests
import time


def date2timestamp(datex: date) -> int:
    return int(time.mktime((datex.year, datex.month, datex.day, 0, 0, 0, 0, 0, 0)))


# Note: This class must be named Fetcher in order for dynamic load to find it.
class Fetcher(AbstractFetcher):

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ONE-TIME CHARGES
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _process_checkouts(self, checkouts):
        assert len(checkouts) < self.limit
        for checkout in checkouts:

            if not checkout['state'].startswith("captured"):
                continue

            desc = checkout['short_description']
            if checkout['checkout_id'] in [1877931854, 390559320]:
                # These are membership purchases that were erroneously entered as donations.
                months = 6
            elif checkout['amount'] == 20 \
             and desc == "Recurring Payment to Donation" \
             and md5(checkout['payer_name'].encode('utf-8')).hexdigest() == "95c53a5e254c1847ad8526b625862294":
                # Dale says that this recurring donation should be treated as a grandfathered membership.
                # I'm checking against md5 of the payer-name so I don't have personal info in source.
                months = 1
            elif desc.startswith("One Month Membership"): months = 1
            elif desc.startswith("Three Month Membership"): months = 3
            elif desc.startswith("Six Month Membership"): months = 6
            elif desc.startswith("Recurring Payment to Dues-Paying Member"): months = 1
            elif desc.startswith("Payment to Dues-Paying Member ONE-TIME"): months = 1
            else:
                # TODO: Process these!
                if desc.endswith("Event Payment"): continue
                if desc.startswith("Recurring Payment to Donation"): continue
                if desc.startswith("Payment to Donation at"): continue
                print("Didn't recognize: "+desc)
                continue

            if desc.endswith("+ 1 family member"): family = 1
            elif desc.endswith("+ 2 family member"): family = 2
            elif desc.endswith("+ 3 family member"): family = 3
            elif desc.endswith("+ 4 family member"): family = 4
            elif desc.endswith("+ 5 family member"): family = 5
            elif desc.endswith("+ 6 family member"): family = 6
            else: family = 0

            sale = Sale()
            sale.payment_method = Sale.PAID_BY_WEPAY
            sale.payer_email = checkout['payer_email']
            sale.payer_name = checkout['payer_name']
            sale.sale_date = date.fromtimestamp(int(checkout['create_time']))  # TODO: This is UTC timezone.
            sale.total_paid_by_customer = Decimal(checkout['gross'])  # Docs: "The total dollar amount paid by the payer"
            sale.processing_fee = Decimal(checkout['fee']) + Decimal(checkout['app_fee'])
            sale.ctrlid = "{}:{}".format(self.CTRLID_PREFIX, checkout['checkout_id'])
            django_sale = self.upsert(sale)

            mship = Membership()
            mship.sale = Sale(id=django_sale['id'])
            mship.sale_price = sale.total_paid_by_customer
            if checkout['fee_payer'] == 'payer': mship.sale_price -= sale.processing_fee
            if family > 0: mship.sale_price -= Decimal(10.00) * Decimal(family)
            mship.ctrlid = checkout['checkout_id']
            mship.start_date = sale.sale_date
            mship.end_date = mship.start_date + relativedelta(months=months, days=-1)
            self.upsert(mship)

            for n in range(family):
                fam = Membership()
                fam.sale            = mship.sale
                fam.sale_price      = 10.00
                fam.membership_type = Membership.MT_FAMILY
                fam.start_date      = mship.start_date
                fam.end_date        = mship.end_date
                fam.ctrlid          = "{}:{}".format(mship.ctrlid, n)
                self.upsert(fam)

    def _process_checkout_data(self, account):
        URL = "https://wepayapi.com/v2/checkout/find"

        window_start = date(2013, 12, 1)
        while window_start < date.today():
            window_start = window_start + relativedelta(months=+1)
            window_end = window_start + relativedelta(months=+1)
            post_data = {
                'account_id': account,
                'start_time': str(date2timestamp(window_start)),
                'end_time': str(date2timestamp(window_end)),
                'limit': str(self.limit)
            }
            response = self.session.post(URL, post_data, headers=self.auth_headers)
            checkouts = response.json()
            self._process_checkouts(checkouts)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # SUBSCRIPTION-RELATED CHARGES
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _process_subscription_charges(self, charges, subscription, family):
        for charge in charges:

            if not charge["state"].startswith("captured"):
                if not charge["state"] == "failed": print(charge["state"])
                continue

            sale = Sale()
            sale.payer_name = subscription['payer_name']
            sale.payer_email = subscription['payer_email']
            if subscription['fee_payer'] == "payer":
                print("Fee is paid by payer. Situation has not yet been analyzed.")
            sale.payment_method = Sale.PAID_BY_WEPAY
            sale.sale_date = date.fromtimestamp(int(charge['create_time']))  # TODO: This is UTC timezone.
            sale.total_paid_by_customer = charge["amount"]
            sale.processing_fee = charge["fee"]
            sale.ctrlid = "{}:{}".format(self.CTRLID_PREFIX, charge['subscription_charge_id'])
            django_sale = self.upsert(sale)

            mship = Membership()
            mship.sale = Sale(id=django_sale['id'])
            mship.sale_price = sale.total_paid_by_customer
            if subscription['fee_payer'] == 'payer': mship.sale_price -= sale.processing_fee
            if family > 0: mship.sale_price -= Decimal(10.00) * Decimal(family)
            mship.ctrlid = "{}:{}".format(self.CTRLID_PREFIX, charge['subscription_charge_id'])
            mship.start_date = sale.sale_date
            mship.end_date = mship.start_date + relativedelta(months=1, days=-1)
            self.upsert(mship)

            for n in range(family):
                fam = Membership()
                fam.sale            = mship.sale
                fam.sale_price      = 10.00
                fam.membership_type = Membership.MT_FAMILY
                fam.start_date      = mship.start_date
                fam.end_date        = mship.end_date
                fam.ctrlid          = "{}:{}".format(mship.ctrlid, n)
                self.upsert(fam)

    def _process_subscriptions(self, subscriptions, family_count):
        for subscription in subscriptions:
            response = self.session.post(
                "https://wepayapi.com/v2/subscription_charge/find",  # subscription_id --> list of charges
                {'subscription_id': subscription['subscription_id']},
                headers = self.auth_headers)
            charges = response.json()
            self._process_subscription_charges(charges, subscription, family_count)

    def _process_plans(self, plans):
        for plan in plans:

            if plan["number_of_subscriptions"] == 0:
                continue

            if not plan['name'].startswith("Membership"):
                print("Unexpected subscription plan: " + plan['name'])
                continue

            if plan['name'] == "Membership":
                family_count = 0
            else:
                countstr = plan['name'].replace("Membership +", "")
                family_count = int(countstr)

            response = self.session.post(
                "https://wepayapi.com/v2/subscription/find",  # subscription_plan_id --> list of subscriptions
                {'subscription_plan_id': plan["subscription_plan_id"]},
                headers = self.auth_headers)
            subscriptions = response.json()
            self._process_subscriptions(subscriptions, family_count)

    def _process_subscription_data(self):
        response = self.session.get(
            "https://wepayapi.com/v2/subscription_plan/find",  # No args --> list of all subscription plans
            headers=self.auth_headers)
        plans = response.json()
        self._process_plans(plans)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # INIT & ABSTRACT METHODS
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def __init__(self):

        self.session = requests.Session()
        self.limit = 1000  # The max number of checkouts returned per find.
        self.CTRLID_PREFIX = "WE"

        accounts = input("WePay Accounts: ").split()
        rest_token = input("WePay Token: ")  # So far, same token works for all accts.

        if len(accounts)+len(rest_token) == 0:
            self.skip = True
        else:
            self.skip = False
            self.accounts = accounts
            self.auth_headers = {'Authorization': "Bearer " + rest_token}

    def fetch(self):

        self._process_subscription_data()
        for account in self.accounts: self._process_checkout_data(account)
        self._fetch_complete()
