import abc
import twocheckout
from decimal import Decimal
from members.models import PaidMembership
from dateutil.relativedelta import relativedelta
from dateutil import parser
from datetime import date
from hashlib import md5
import time
import requests
import lxml.html


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Fetcher(object):  # The "ET" in "ETL"

    __metalass__ = abc.ABCMeta

    @abc.abstractmethod
    def generate_paid_memberships(self):
        """Yields an unsaved PaidMembership instance"""
        return


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# TODO: MOVE XEROCRAFT-SPECIFIC FETCHERS, BELOW, INTO xerocraft.fetchers

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TwoCheckoutFetcher(Fetcher):

    def gen_from_lineitems(self, lineitems):

        if len(lineitems) > 1:
            print("WARNING: More than two line items in invoice.")
            return

        for lineitem in lineitems:
            amt = Decimal(lineitem.customer_amount)
            assert amt >= 50, "Didn't expect line item amount < 50."
            assert amt % 10 == 0, "Didn't expect line item amount that's not a multiple of 10."
            assert len(lineitem.options) <= 1
            assert lineitem.status in ["bill", "refund"]

            pm = PaidMembership()
            pm.paid_by_member = amt
            pm.family_count   = str(int((amt-50)/10))
            yield pm

    def gen_from_invoices(self, invoices):
        invoices_to_skip = ['105756939333']
        for invoice in invoices:

            # if invoice.invoice_id in invoices_to_skip: continue

            paid_status = invoice.payout_status.startswith("Paid")
            captured_status = invoice.payout_status.startswith("Captured")
            if not (paid_status or captured_status):
                # See http://help.2checkout.com/articles/Knowledge_Article/Payout-Status
                continue

            for pm in self.gen_from_lineitems(invoice.lineitems):
                pm.processing_fee = Decimal(invoice.fees_2co)
                pm.payment_date   = parser.parse(invoice.date_placed).date()
                pm.start_date     = pm.payment_date  # Inclusive
                pm.end_date       = pm.start_date + relativedelta(months=+1, days=-1)  # Inclusive
                pm.payment_method = PaidMembership.PAID_BY_2CO
                pm.ctrlid         = invoice.invoice_id
                yield pm

    def gen_from_sales(self, sales):
        for sale in sales:  # sale summary
            sale = twocheckout.Sale.find({'sale_id': sale.sale_id})  # sale detail

            for pm in self.gen_from_invoices(sale.invoices):
                nameparts = [
                    sale.customer.first_name,
                    sale.customer.middle_initial,
                    sale.customer.last_name
                ]
                nameparts = [part for part in nameparts if part is not None and len(part)>0]
                namestr = " ".join(nameparts)
                pm.payer_email = sale.customer.email_address
                pm.payer_name  = namestr
                yield pm

    def generate_paid_memberships(self):
        userid = input("2CO userid: ")
        password = input("2CO password: ")
        twocheckout.Api.credentials({'username': userid, 'password': password})
        max_page_num = 99
        page_num = 1
        while page_num <= max_page_num:
            # opts = {'cur_page':page_num, 'pagesize':100, 'customer_name':"Glen Olson"}
            opts = {'cur_page': page_num, 'pagesize': 100}
            page_info, sales_on_page = twocheckout.Sale.list(opts)
            for pm in self.gen_from_sales(sales_on_page):
                yield pm
            max_page_num = page_info.last_page
            page_num += 1


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def date2timestamp(date):
    return int(time.mktime((date.year, date.month, date.day, 0, 0, 0, 0, 0, 0)))


class WePayFetcher(Fetcher):

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


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SquareFetcher(Fetcher):

    session = requests.Session()

    uninteresting = [
        "Donation",
        "Workshop Fee",
        "Custom Amount",  # I believe this is a donation.
        "Refill Soda Account",
        "Holiday Gift Card (6 months)",
        "Bumper Sticker",
        "Medium Sticker",
    ]

    def gen_from_itemizations(self, itemizations, payment_id, payment_date, payment_total, payment_fee):
        for item in itemizations:

            family_count = None

            if payment_id == '0JFN0loJ0kcy8DXCvuDVwwMF':
                # This is a work trade payment that was erroneously entered as a custom payment.
                # So we do this special processing to ingest it as a 1 month Work Trade membership.
                family_count = 0
                months = 1
                short_item_code = "WT"
                membership_type = PaidMembership.MT_WORKTRADE
            elif item['name'] in self.uninteresting:
                continue
            elif item['name'] == "One Month Membership":
                months = 1
                short_item_code = "1MM"
                membership_type = PaidMembership.MT_REGULAR
            elif item['name'] in ["Work-Trade Fee", "Work-Trade Dues"]:
                months = 1
                short_item_code = "WT"
                membership_type = PaidMembership.MT_WORKTRADE
            else:
                print("Didn't recognize item name: "+item['name'])
                continue

            for modifier in item["modifiers"]:
                if modifier["name"] == "Just myself": family_count = 0
                elif modifier["name"] == "1 add'l family member": family_count = 1
                elif modifier["name"] == "2 add'l family members": family_count = 2
                elif modifier["name"] == "3 add'l family members": family_count = 3
                elif modifier["name"] == "4 add'l family members": family_count = 4
                elif modifier["name"] == "5 add'l family members": family_count = 5
            if family_count is None:
                print("Couldn't determine family count for {}:{}".format(payment_id, short_item_code))

            quantity = int(float(item['quantity']))
            for n in range(1, quantity+1):
                pm = PaidMembership()
                pm.membership_type = membership_type
                pm.payment_method = PaidMembership.PAID_BY_SQUARE
                pm.ctrlid = "{}:{}:{}".format(payment_id, short_item_code, str(n))
                pm.payer_email = ""  # Annoyingly, not provided by Square.
                pm.payer_name = ""  # Annoyingly, not provided by Square.
                pm.payer_notes = item.get("notes", "")
                pm.payment_date = payment_date
                pm.start_date = pm.payment_date
                if pm.membership_type == PaidMembership.MT_WORKTRADE:
                    # This is a guess, but it will usually be right.
                    # TODO: Add better logic once people start choosing month modifier.
                    pm.start_date = pm.start_date.replace(day=1)
                pm.end_date = pm.start_date + relativedelta(months=months, days=-1)
                pm.family_count = family_count
                pm.paid_by_member = float(item['gross_sales_money']['amount']) / (quantity * 100.0)
                pm.processing_fee = pm.paid_by_member/payment_total * payment_fee  # Fee is divided among items.

                yield pm

    def get_name_from_receipt(self, url):
        response = self.session.get(url)
        parsed_page = lxml.html.fromstring(response.text)
        if parsed_page is None: raise AssertionError("Couldn't parse receipts page")
        names = parsed_page.xpath("//div[contains(@class,'name_on_card')]/text()")
        return names[0] if len(names)>0 else ""

    def gen_from_payment(self, payments):
        for payment in payments:
            payment_id = payment["id"]
            payment_date = parser.parse(payment["created_at"]).date()
            payment_fee = -1.0 * float(payment["processing_fee_money"]["amount"]) / 100.0
            payment_total = float(payment["gross_sales_money"]["amount"]) / 100.0
            receipt_name = None  # Only get it if we know we need it. We won't need it for every payment.
            itemizations = payment['itemizations']
            for pm in self.gen_from_itemizations(itemizations, payment_id, payment_date, payment_total, payment_fee):
                pm.payer_email = ""  # Annoyingly, not provided by Square.
                if receipt_name is None:  # We now know we need it, so get it.
                    receipt_name = self.get_name_from_receipt(payment['receipt_url'])
                pm.payer_name = receipt_name
                yield pm

    def generate_paid_memberships(self):

        merchant_id = input("Square Merchant ID: ")
        rest_token = input("Square Token: ")

        get_headers = {
            'Authorization': "Bearer " + rest_token,
            'Accept': "application/json",
        }

        post_put_headers = {
            'Authorization': "Bearer " + rest_token,
            'Accept': "application/json",
            'Content-Type': "application/json",
        }

        payments_url = "https://connect.squareup.com/v1/{}/payments".format(merchant_id)

        window_start = date(2013, 12, 1)
        while window_start < date.today():
            window_start = window_start + relativedelta(months=+1)
            window_end = window_start + relativedelta(months=+1)
            get_data = {
                'begin_time': window_start.isoformat(),
                'end_time': window_end.isoformat(),
                'limit': str(200)  # Max allowed by Square
            }
            response = self.session.get(payments_url, params=get_data, headers=get_headers)
            payments = response.json()
            for pm in self.gen_from_payment(payments):
                yield pm