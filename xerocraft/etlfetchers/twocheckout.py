from xerocraft.etlfetchers.abstractfetcher import AbstractFetcher
from members.models import Membership
from books.models import Sale
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import twocheckout
from decimal import Decimal


# Note: This class must be named Fetcher in order for dynamic load to find it.
class Fetcher(AbstractFetcher):

    def _process_lineitems(self, djgo_sale, lineitems):

        if len(lineitems) > 1:
            print("WARNING: More than two line items in invoice.")

        for lineitem in lineitems:
            amt = Decimal(lineitem.customer_amount)
            assert amt >= 50, "Didn't expect line item amount < 50."
            assert amt % 10 == 0, "Didn't expect line item amount that's not a multiple of 10."
            assert len(lineitem.options) <= 1
            assert lineitem.status in ["bill", "refund"]

            mship = Membership()

            mship.sale = Sale(id=djgo_sale['id'])
            mship.start_date    = parse(djgo_sale['sale_date']).date()  # Inclusive
            mship.end_date      = mship.start_date + relativedelta(months=+1, days=-1)  # Inclusive
            mship.sale_price    = amt
            mship.ctrlid        = "2CO:{}:{}".format(lineitem.invoice_id, lineitem.lineitem_id)
            self.upsert(mship)

            family = int((amt-50)/10)
            for n in range(family):
                fam = Membership()
                fam.sale            = mship.sale
                fam.sale_price      = 10
                fam.membership_type = Membership.MT_FAMILY
                fam.start_date      = mship.start_date
                fam.end_date        = mship.end_date
                fam.ctrlid          = "{}:{}".format(mship.ctrlid, n)
                self.upsert(fam)

    def _process_invoices(self, invoices):
        invoices_to_skip = [
            '105756939333',  # Jeremy's initial test.
            '205811359970',  # Adrian refunded this. Code to handle refunds is not yet written.
        ]
        for invoice in invoices:

            if invoice.invoice_id in invoices_to_skip:
                continue

            paid_status = invoice.payout_status.startswith("Paid")
            captured_status = invoice.payout_status.startswith("Captured")
            if not (paid_status or captured_status):
                # See http://help.2checkout.com/articles/Knowledge_Article/Payout-Status
                continue

            new_sale = Sale()

            new_sale.payer_name             = self.payer_name
            new_sale.payer_email            = self.payer_email
            new_sale.processing_fee         = Decimal(invoice.fees_2co)
            new_sale.sale_date              = parse(invoice.date_placed).date()
            new_sale.payment_method         = Sale.PAID_BY_2CO
            new_sale.method_detail          = self.method_detail
            new_sale.ctrlid                 = "2CO:"+invoice.invoice_id
            new_sale.total_paid_by_customer = invoice.customer_total
            djgo_sale = self.upsert(new_sale)
            self._process_lineitems(djgo_sale, invoice.lineitems)

    def _process_sales(self, sales):
        for tco_sale_summary in sales:  # sale summary
            tco_sale = twocheckout.Sale.find({'sale_id': tco_sale_summary.sale_id})  # sale detail
            nameparts = [
                tco_sale.customer.first_name,
                tco_sale.customer.middle_initial,
                tco_sale.customer.last_name
            ]
            nameparts = [part for part in nameparts if part is not None and len(part)>0]
            self.payer_name = " ".join(nameparts)
            self.payer_email = tco_sale.customer.email_address
            self.method_detail = self.card_type(tco_sale.customer.pay_method.first_six_digits)
            self._process_invoices(tco_sale.invoices)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # INIT & ABSTRACT METHODS
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def __init__(self):
        userid = input("2Checkout userid: ")
        password = input("2Checkout password: ")
        if len(userid)+len(password) == 0:
            self.skip = True
        else:
            twocheckout.Api.credentials({'username': userid, 'password': password})
            self.skip = False

    def fetch(self):

        max_page_num = 99
        page_num = 1
        while page_num <= max_page_num:
            opts = {'cur_page': page_num, 'pagesize': 100}
            page_info, sales_on_page = twocheckout.Sale.list(opts)
            self._process_sales(sales_on_page)
            max_page_num = page_info.last_page
            page_num += 1

        self._fetch_complete()