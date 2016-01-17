import abc
import twocheckout
from decimal import Decimal
from dateutil import parser
from members.models import PaidMembership
from dateutil.relativedelta import relativedelta
from dateutil import parser


class Fetcher(object):

    __metalass__ = abc.ABCMeta

    @abc.abstractmethod
    def generate_payments(self):
        """Yields an unsaved PaidMembership instance"""
        return


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

            if not invoice.payout_status.startswith("Paid"):
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


