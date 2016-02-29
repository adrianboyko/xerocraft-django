
from xerocraft.etlfetchers.abstractfetcher import AbstractFetcher
from members.models import PaidMembership
from hashlib import md5
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import requests
import time


def date2timestamp(date):
    return int(time.mktime((date.year, date.month, date.day, 0, 0, 0, 0, 0, 0)))


# Note: This class must be named Fetcher in order for dynamic load to find it.
class Fetcher(AbstractFetcher):

    session = requests.Session()
    auth_headers = None

    limit = 1000  # The max number of checkins returned per find.

    def gen_from_checkouts(self, checkouts):
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
                if desc.endswith("Event Payment"): continue
                if desc.startswith("Recurring Payment to Donation"): continue
                if desc.startswith("Payment to Donation at"): continue
                print(desc)
                continue

            if desc.endswith("+ 1 family member"): family = 1
            elif desc.endswith("+ 2 family member"): family = 2
            elif desc.endswith("+ 3 family member"): family = 3
            elif desc.endswith("+ 4 family member"): family = 4
            elif desc.endswith("+ 5 family member"): family = 5
            elif desc.endswith("+ 6 family member"): family = 6
            else: family = 0

            pm = PaidMembership()
            pm.payment_method = PaidMembership.PAID_BY_WEPAY
            pm.ctrlid = checkout['checkout_id']
            pm.payer_email = checkout['payer_email']
            pm.payer_name = checkout['payer_name']
            pm.family_count = family
            pm.payment_date = date.fromtimestamp(int(checkout['create_time']))  # TODO: This is UTC timezone.
            pm.start_date = pm.payment_date
            pm.end_date = pm.start_date + relativedelta(months=months, days=-1)
            pm.paid_by_member = Decimal(checkout['gross'])  # Docs: "The total dollar amount paid by the payer"
            pm.processing_fee = Decimal(checkout['fee']) + Decimal(checkout['app_fee'])
            yield pm

    def gen_from_account_charges(self, accounts):
        for account in accounts:
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
                for pm in self.gen_from_checkouts(checkouts):
                    yield pm

    def gen_from_subscription_charges(self, charges):
        for charge in charges:

            if not charge["state"].startswith("captured"):
                if not charge["state"] == "failed": print(charge["state"])
                continue

            pm = PaidMembership()

            pm.payment_method = PaidMembership.PAID_BY_WEPAY
            pm.ctrlid = charge['subscription_charge_id']

            pm.payment_date = date.fromtimestamp(int(charge['create_time']))  # TODO: This is UTC timezone.
            pm.start_date = pm.payment_date
            pm.end_date = pm.start_date + relativedelta(months=1, days=-1)  # REVIEW: Use "end_time" instead?

            pm.paid_by_member = charge["amount"]
            pm.processing_fee = charge["fee"]

            yield pm

    def gen_from_plan_subscriptions(self, subscriptions):
        for subscription in subscriptions:
            response = self.session.post(
                "https://wepayapi.com/v2/subscription_charge/find",  # subscription_id --> list of charges
                {'subscription_id': subscription['subscription_id']},
                headers = self.auth_headers)
            charges = response.json()
            for pm in self.gen_from_subscription_charges(charges):
                pm.payer_name = subscription['payer_name']
                pm.payer_email = subscription['payer_email']
                pm.payer_notes = ""
                if subscription['fee_payer'] == "payer":
                    print("Fee is paid by payer. Situation has not yet been analyzed.")
                yield pm

    def gen_from_subscription_plans(self, plans):
        for plan in plans:

            if plan["number_of_subscriptions"] == 0: continue

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
            for pm in self.gen_from_plan_subscriptions(subscriptions):
                pm.family_count = family_count
                yield pm

    def gen_from_account_subscriptions(self, accounts):
        for account in accounts:
            response = self.session.get(
                "https://wepayapi.com/v2/subscription_plan/find",  # No args --> list of all subscription plans
                headers=self.auth_headers)
            plans = response.json()
            for pm in self.gen_from_subscription_plans(plans):
                yield pm

    def generate_paid_memberships(self):
        accounts = input("WePay Accounts: ").split()
        rest_token = input("WePay Token: ")  # So far, same token works for all accts.
        self.auth_headers = {'Authorization': "Bearer " + rest_token}

        # Process subscriptions and associated charges.
        for pm in self.gen_from_account_subscriptions(accounts):
            yield pm

        # Process the regular one-time checkouts.
        for pm in self.gen_from_account_charges(accounts):
            yield pm

