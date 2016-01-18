import abc
import twocheckout
from decimal import Decimal
from members.models import PaidMembership
from dateutil.relativedelta import relativedelta
from dateutil import parser
from datetime import date
import time
import requests


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Fetcher(object):  # The "ET" in "ETL"

    __metalass__ = abc.ABCMeta

    @abc.abstractmethod
    def generate_payments(self):
        """Yields an unsaved PaidMembership instance"""
        return


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TwoCheckoutFetcher(Fetcher):

    def generate_from_lineitems(self, lineitems):

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

    def generate_from_invoices(self, invoices):
        invoices_to_skip = ['105756939333']
        for invoice in invoices:

            # if invoice.invoice_id in invoices_to_skip: continue

            paid_status = invoice.payout_status.startswith("Paid")
            captured_status = invoice.payout_status.startswith("Captured")
            if not (paid_status or captured_status):
                # See http://help.2checkout.com/articles/Knowledge_Article/Payout-Status
                continue

            for pm in self.generate_from_lineitems(invoice.lineitems):
                pm.processing_fee = Decimal(invoice.fees_2co)
                pm.payment_date   = parser.parse(invoice.date_placed).date()
                pm.start_date     = pm.payment_date  # Inclusive
                pm.end_date       = pm.start_date + relativedelta(months=+1, days=-1)  # Inclusive
                pm.payment_method = PaidMembership.PAID_BY_2CO
                pm.ctrlid         = invoice.invoice_id
                yield pm

    def generate_from_sales(self, sales):
        for sale in sales:  # sale summary
            sale = twocheckout.Sale.find({'sale_id': sale.sale_id})  # sale detail

            for pm in self.generate_from_invoices(sale.invoices):
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

    def generate_payments(self):
        userid = input("2CO userid: ")
        password = input("2CO password: ")
        twocheckout.Api.credentials({'username': userid, 'password': password})
        max_page_num = 99
        page_num = 1
        while page_num <= max_page_num:
            # opts = {'cur_page':page_num, 'pagesize':100, 'customer_name':"Glen Olson"}
            opts = {'cur_page': page_num, 'pagesize': 100}
            page_info, sales_on_page = twocheckout.Sale.list(opts)
            for pm in self.generate_from_sales(sales_on_page):
                yield pm
            max_page_num = page_info.last_page
            page_num += 1


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def date2timestamp(date):
    return int(time.mktime((date.year, date.month, date.day, 0, 0, 0, 0, 0, 0)))


class WePayFetcher(Fetcher):

    session = requests.Session()

    limit = 1000  # The max number of checkins returned per find.

    def generate_from_checkouts(self, checkouts):
        assert len(checkouts) < self.limit
        for checkout in checkouts:

            if not checkout['state'].startswith("captured"):
                continue

            desc = checkout['short_description']
            if desc.startswith("One Month Membership"): months = 1
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
            pm.payment_date = date.fromtimestamp(int(checkout['create_time']))
            pm.start_date = pm.payment_date
            pm.end_date = pm.start_date + relativedelta(months=months, days=-1)
            pm.paid_by_member = Decimal(checkout['gross'])  # Docs: "The total dollar amount paid by the payer"
            pm.processing_fee = Decimal(checkout['fee']) + Decimal(checkout['app_fee'])
            yield pm

    def generate_payments(self):
        accounts = input("WePay Accounts: ").split()
        rest_token = input("WePay Token: ")  # So far, same token works for all accts.
        auth_headers = {'Authorization': "Bearer " + rest_token}

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
                response = self.session.post(URL, post_data, headers=auth_headers)
                checkouts = response.json()
                for pm in self.generate_from_checkouts(checkouts):
                    yield pm
