
# Standard
import sys
from decimal import Decimal
from datetime import datetime, date

# Third Party
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import paypalrestsdk as sdk
from django.utils.timezone import localtime

# Local
from bzw_ops.etlfetchers.abstractfetcher import AbstractFetcher
from members.models import Membership, Member, MembershipGiftCardReference
from books.models import Sale, MonetaryDonation, OtherItem, OtherItemType
from xis.xerocraft_org_utils.paypalscraper import PaypalScraper


# Note: This class must be named Fetcher in order for dynamic load to find it.
class Fetcher(AbstractFetcher):

    # TODO: Prices should be factored out in to something that's available to all fetchers.
    prices = {
        1: Decimal(50.00),
        2: Decimal(90.00),
        3: Decimal(132.00),
        6: Decimal(225.00),
        12: Decimal(450.00)
    }

    def _member_and_family(self, sale: Sale, months: int):

        primary_membership_price = Fetcher.prices[months]
        assert primary_membership_price <= sale.total_paid_by_customer
        remaining = sale.total_paid_by_customer - primary_membership_price
        assert remaining % Decimal(10.00) == 0  # Additional family members should be $10/mo
        fam_count = int(remaining) // 10 // months

        mship = Membership()
        mship.sale = sale
        mship.membership_type = Membership.MT_REGULAR
        mship.ctrlid = "{}:P".format(sale.ctrlid)
        mship.start_date = sale.sale_date
        mship.end_date = mship.start_date + relativedelta(months=months, days=-1)
        mship.sale_price = Decimal(primary_membership_price)
        self.upsert(mship)

        for f in range(1, fam_count+1):
            mship.membership_type = Membership.MT_FAMILY
            mship.ctrlid = "{}:{}".format(sale.ctrlid, f)
            mship.sale_price = Decimal(months*10.00)
            self.upsert(mship)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ONE-TIME PAYMENTS created up by Xerocraft.org (for class donations, fees)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _process_donation_item(self, sale: Sale, description: str):
        don = MonetaryDonation()
        don.ctrlid = "{}:{}".format(self.CTRLID_PREFIX, sale.id)
        don.sale = sale
        don.amount = sale.total_paid_by_customer
        # TODO: Add earmark
        self.upsert(don)

    def _process_non_recurring_membership_item(self, sale: Sale, description: str):
        """ Takes a sale and a descripton like MSHIP_06_MONTH and creates a membership """
        months = description.replace("MSHIP_", "")
        months = months.replace("_MONTH", "")
        months = int(months)
        self._member_and_family(sale, months)

    def _process_unknown_item(self, sale:Sale):

        typepk = self._get_id(self.URLS[OtherItemType], {'name': "Unknown"})
        if typepk is None:
            print("Server does not have an 'unknown' item type.")
            return

        other = OtherItem()
        other.ctrlid = "{}:{}".format(self.CTRLID_PREFIX, sale.id)
        other.type = OtherItemType(id=typepk)
        other.sale = sale
        other.sale_price = sale.total_paid_by_customer
        other.qty_sold = 1
        self.upsert(other)

    PAYMENTS_TO_IGNORE = [
        'PAY-83R23166VG575420MK7EIF3Y',  # A test by Kyle that doesn't seem to match other refund cases.
    ]

    def _process_payment(self, payment: sdk.Payment):
        payment_id = payment['id']
        if payment_id in self.PAYMENTS_TO_IGNORE:
            return
        state = payment['state']  # e.g. 'approved'
        when_datetime = parse(payment['create_time'])  # type: datetime
        when_local_date = localtime(when_datetime).date()
        if 'payer' not in payment:
            print(payment)
            return
        if 'payer_info' not in payment['payer']:
            print(payment)
            return
        who_fname = payment['payer']['payer_info']['first_name']
        who_lname = payment['payer']['payer_info']['last_name']
        try:
            who_email = payment['payer']['payer_info']['email']
        except:
            who_email = ""

        assert len(payment['transactions']) == 1, "Code can't yet deal with multiple transactions payment."
        transaction = payment['transactions'][0]
        payment_amount = transaction['amount']['total']
        if 'custom' in transaction:  # Xerocraft.org puts an indication of what was paid for in "custom"
            what = transaction['custom']
        else:
            what = None

        resources = transaction['related_resources']
        sale_amt = None
        refund_amt = None
        if len(resources) == 0:
            # This has only been observed in a test transaction generated by Kyle
            print("K", end="")
            return
        for resource in resources:
            if 'sale' in resource:
                sale = resource['sale']
                if sale_amt is not None:
                    print("WARNING (not handled): Multiple sale resources in sale to " + who_email + " on " + str(when_local_date))
                sale_amt = float(sale['amount']['total'])
                pay_mode = sale['payment_mode']  # e.g. 'INSTANT_TRANSFER'
                trans_fee = float(sale['transaction_fee']['value'])
            if 'refund' in resource:
                refund = resource['refund']
                if refund['state'] is "failed":
                    continue
                if refund_amt is not None:
                    print("WARNING (not handled): Multiple refunds in sale to " + who_email + " on " + str(when_local_date))
                refund_amt = float(refund['amount']['total'])
            if sale_amt is not None and refund_amt is not None:
                # NOTE: Refunds will require manual processing. Adjusted transactions should be marked "protected".
                if sale_amt == refund_amt:
                    print("R", end="")
                    return
                else:
                    print("Code doesn't yet deal with partial refunds. Sale was to "+who_email+" on "+str(when_local_date))
                    return

        sale = Sale()
        sale.payment_method = Sale.PAID_BY_PAYPAL
        sale.payer_email = who_email
        sale.payer_name = "{} {}".format(who_fname, who_lname)
        sale.sale_date = when_local_date
        sale.total_paid_by_customer = Decimal(sale_amt)  # The full amount paid by the person, including payment processing fee IF CUSTOMER PAID IT.
        sale.processing_fee = Decimal(trans_fee)
        sale.ctrlid = "{}:{}".format(self.CTRLID_PREFIX, payment_id)
        django_sale = self.upsert(sale)
        sale.id = django_sale['id']

        if django_sale["protected"] == True:
            # If the sale is protected then all details are also protected.
            # Otherwise there's no way to protect a deletion.
            return

        if what is None:
            self._process_unknown_item(sale)
        elif what.startswith("DON_"):
            self._process_donation_item(sale, what)
        elif what.startswith("MSHIP_"):
            self._process_non_recurring_membership_item(sale, what)
        else:
            print("Unkown item: "+what)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # RECURRING PAYMENTS set up by Xerocraft.org (for memberships)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _process_recurring_payment(self, agreement: sdk.BillingAgreement, transaction):
        when_datetime = parse(transaction["time_stamp"])  # type: datetime
        when_local_date = localtime(when_datetime).date()

        payer_name = transaction["payer_name"]
        payer_email = transaction["payer_email"]
        paid_amount = transaction["amount"]["value"]
        net_amount = transaction["net_amount"]["value"]
        fee_amount = str(Decimal(-1.0) * Decimal(transaction["fee_amount"]["value"]))
        trans_id = transaction["transaction_id"]
        fam_count = int((float(paid_amount)-50.00)/10.00)

        assert transaction["net_amount"]["currency"] == "USD"
        assert transaction["fee_amount"]["currency"] == "USD"
        assert transaction["amount"]["currency"] == "USD"
        assert transaction["time_zone"] == "GMT"
        assert float(paid_amount) >= 50.00

        sale = Sale()
        sale.payment_method = Sale.PAID_BY_PAYPAL
        sale.payer_email = payer_email
        sale.payer_name = payer_name
        sale.sale_date = when_local_date
        sale.total_paid_by_customer = Decimal(paid_amount)  # The full amount paid by the person, including payment processing fee IF CUSTOMER PAID IT.
        sale.processing_fee = Decimal(fee_amount)
        sale.ctrlid = "{}:{}".format(self.CTRLID_PREFIX, trans_id)
        django_sale = self.upsert(sale)
        sale.id = django_sale['id']

        if django_sale["protected"]:
            # If the sale is protected then all details are also protected.
            # Otherwise there's no way to protect a deletion.
            return

        self._member_and_family(sale, 1)

    def _process_agreement(self, agreement: sdk.BillingAgreement):
        transactions = agreement.search_transactions("2016-01-01", date.today().isoformat())
        for transaction in transactions['agreement_transaction_list']:
            stat = transaction["status"]
            if stat == 'Created':
                pass  # Might want to do something with this, eventually.
            elif stat == 'Completed':
                self._process_recurring_payment(agreement, transaction)
            elif stat == 'Canceled':
                pass  # Might want to do something with this, eventually.
            else:
                print("Unrecognized status: " + stat)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # INIT & ABSTRACT METHODS
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def __init__(self):

        self.CTRLID_PREFIX = "PP"

        mode = "live"
        client_id = input("PayPal Client ID: ")
        client_secret = input("PayPal Secret: ")

        if len(client_id) * len(client_secret) == 0:
            self.skip = True
        else:
            self.skip = False
            sdk.configure({
                'mode': mode,
                'client_id': client_id,
                'client_secret': client_secret,
            })

    def fetch(self):

        # Process billing agreements that were set up by the xerocraft.org website:
        scraper = PaypalScraper()
        agreement_ids = scraper.scrape_agreement_ids()
        for agreement_id in agreement_ids:
            agreement = sdk.BillingAgreement.find(agreement_id)
            self._process_agreement(agreement)

        # Process all other payments:
        next_id = None
        while True:
            hist_params = {"count": 20}
            if next_id is not None:
                hist_params["start_id"] = next_id
            else:
                hist_params["start_time"] = "2015-03-06T11:00:00Z"
            payment_history = sdk.Payment.all(hist_params)
            payments = payment_history.payments
            for payment in payments:
                self._process_payment(payment)
            next_id = payment_history.next_id
            if next_id is None:
                break

        self._fetch_complete()