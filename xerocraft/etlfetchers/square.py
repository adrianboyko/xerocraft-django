from xerocraft.etlfetchers.abstractfetcher import AbstractFetcher
from members.models import Membership, Member, MembershipGiftCardReference
from books.models import Sale, MonetaryDonation, OtherItem, OtherItemType
from datetime import date
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import requests
import requests.exceptions
import lxml
import lxml.html
from decimal import Decimal


# Note: This class must be named Fetcher in order for dynamic load to find it.
class Fetcher(AbstractFetcher):

    squaresession = requests.Session()

    def month_in_str(self, str):
        str = str.lower()
        if "january"     in str: return 1  # TODO: Payment for Jan year X+1 in Dec year X
        elif "february"  in str: return 2
        elif "march"     in str: return 3
        elif "april"     in str: return 4
        elif "may"       in str: return 5
        elif "june"      in str: return 6
        elif "july"      in str: return 7
        elif "august"    in str: return 8
        elif "september" in str: return 9
        elif "october"   in str: return 10
        elif "november"  in str: return 11
        elif "december"  in str: return 12  # TODO: Payment for Dec X-1 in Jan year X
        else: return None

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # PROCESS MEMBERSHIP ITEM
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _process_membership_item(self, sale, item, item_num, membership_type, dur_amt, dur_unit):
        month = self.month_in_str(item['name'])

        family = None
        for modifier in item["modifiers"]:
            lmod = modifier["name"].lower()
            if lmod == "just myself": family = 0
            elif lmod == "1 add'l family member":  family = 1
            elif lmod == "2 add'l family members": family = 2
            elif lmod == "3 add'l family members": family = 3
            elif lmod == "4 add'l family members": family = 4
            elif lmod == "5 add'l family members": family = 5
            if membership_type == Membership.MT_WORKTRADE and month is None:
                month = self.month_in_str(lmod)

        if family is None:
            print("Couldn't determine family count for {}:{}".format(sale['ctrlid'], item_num))
            family = 0

        quantity = int(float(item['quantity']))
        for n in range(1, quantity+1):
            mship = Membership()
            mship.sale = Sale(id=sale['id'])
            mship.membership_type = membership_type
            mship.ctrlid = "{}:{}:{}".format(sale['ctrlid'], item_num, n)
            mship.start_date = parse(sale['sale_date']).date()
            if mship.membership_type == Membership.MT_WORKTRADE:
                mship.start_date = mship.start_date.replace(day=1)  # WT always starts on the 1st.
                if month is not None:  # Hopefully, the buyer specified the month.
                    mship.start_date = mship.start_date.replace(month=month)
            mship.end_date = mship.start_date + relativedelta(**{dur_unit:dur_amt, "days":-1})
            mship.sale_price = Decimal(item['gross_sales_money']['amount']) / Decimal(quantity * 100.0)
            mship.sale_price -= Decimal(10.00) * Decimal(family)
            self.upsert(mship)

            for f in range(family):
                fam = Membership()
                fam.sale            = mship.sale
                fam.sale_price      = 10
                fam.membership_type = Membership.MT_FAMILY
                fam.start_date      = mship.start_date
                fam.end_date        = mship.end_date
                fam.ctrlid          = "{}:{}".format(mship.ctrlid, f)
                self.upsert(fam)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # PROCESS DONATION ITEM
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _process_donation_item(self, sale, item, item_num):

        quantity = int(float(item['quantity']))
        for n in range(1, quantity+1):
            don = MonetaryDonation()
            don.ctrlid = "{}:{}:{}".format(sale['ctrlid'], item_num, n)
            don.sale = Sale(id=sale['id'])
            don.amount = Decimal(item["gross_sales_money"]["amount"]) / Decimal(quantity * 100.0)
            self.upsert(don)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # PROCESS GIFTCARD ITEM
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _process_giftcard_item(self, sale, item, item_num):

        quantity = int(float(item['quantity']))
        for n in range(1, quantity+1):
            cardref = MembershipGiftCardReference()
            cardref.ctrlid = "{}:{}:{}".format(sale['ctrlid'], item_num, n)
            cardref.sale = Sale(id=sale['id'])
            cardref.sale_price = Decimal(item["net_sales_money"]["amount"]) / Decimal(quantity * 100.0)
            self.upsert(cardref)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # PROCESS OTHER ITEM
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    OTHER_ITEM_TYPE_MAP = {
        "Workshop Fee": "Workshop Fee",
        "Bumper Sticker": "Sticker",
        "Medium Sticker": "Sticker",
        "Soda": "Soda",
        "Can of Soda": "Soda",
        "Refill Soda Account": "Refill Soda Account",
    }

    def _process_other_item(self, sale, item, item_num):

        quantity = int(float(item['quantity']))

        if item['name'] not in self.OTHER_ITEM_TYPE_MAP:
            print("Fetcher does not map: "+item['name'])
            return

        mappedname = self.OTHER_ITEM_TYPE_MAP[item['name']]
        typepk = self._get_id(self.URLS[OtherItemType], {'name': mappedname})
        if typepk is None:
            print("Server does not have other item type: "+mappedname)
            return

        other = OtherItem()

        other.type = OtherItemType(id=typepk)
        other.sale = Sale(id=sale['id'])
        other.sale_price = Decimal(item["net_sales_money"]["amount"]) / Decimal(quantity * 100.0)
        other.qty_sold = int(float(item['quantity']))
        other.ctrlid = "{}:{}".format(sale['ctrlid'], item_num)

        self.upsert(other)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # PROCESS ITEMS
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    UNINTERESTING_ITEMS = [
    ]

    DONATION_ITEMS = [
        "Donation",
        "Custom Amount",  # I believe this is a donation.
    ]

    GIFT_CARD_ITEMS = [
        "Holiday Gift Card (6 months)",
        "Holiday Gift Card (3 months)",
        "3 Month Gift Card",
    ]

    WORK_TRADE_ITEMS = [
        "Work-Trade Fee",       # Obsolete, but still necessary for backfills.
        "Work-Trade Dues",      # ditto
        "01 - January Dues",    # ditto
        "02 - February Dues",   # ditto
        "03 - March Dues",      # ditto
        "04 - April Dues",      # ditto
        "05 - May Dues",        # ditto
        "06 - June Dues",       # ditto
        "07 - July Dues",       # ditto
        "08 - August Dues",     # ditto
        "09 - September Dues",  # ditto
        "10 - October Dues",    # ditto
        "11 - November Dues",   # ditto
        "12 - December Dues",   # ditto
        "6hr Work-Trade Dues",  # Current
        "9hr Work-Trade Dues",  # Current
    ]

    def _process_itemizations(self, itemizations: list, sale: dict):
        item_num = 0
        for item in itemizations:
            item_num += 1
            family_count = None

            if item['name'] in self.UNINTERESTING_ITEMS:
                pass

            elif item['name'] == "Workshop Fee":
                # Before 15 March 2016, these were mostly (entirely?) donations.
                # After 15 March 2016, these should only be cost-covering fees (NOT donations)
                sale_date = parse(sale["sale_date"]).date()
                if sale_date < date(2016,3,15):
                    self._process_donation_item(sale, item, item_num)
                else:
                    self._process_other_item(sale, item, item_num)

            elif item['name'] in self.OTHER_ITEM_TYPE_MAP:
                self._process_other_item(sale, item, item_num)

            elif item['name'] in self.DONATION_ITEMS:
                self._process_donation_item(sale, item, item_num)

            elif item['name'] in self.GIFT_CARD_ITEMS:
                self._process_giftcard_item(sale, item, item_num)

            elif item['name'] == "Two Week membership":
                self._process_membership_item(sale, item, item_num, Membership.MT_REGULAR, 1, "weeks")

            elif item['name'] == "One Month Membership":
                self._process_membership_item(sale, item, item_num, Membership.MT_REGULAR, 1, "months")

            elif item['name'] in self.WORK_TRADE_ITEMS:
                self._process_membership_item(sale, item, item_num, Membership.MT_WORKTRADE, 1, "months")

            else:
                print("Didn't recognize item name: "+item['name'])
                continue

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # PROCESS PAYMENTS
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def get_name_from_receipt(self, url):
        while True:
            try:
                response = self.squaresession.get(url)
                parsed_page = lxml.html.fromstring(response.text)
                if parsed_page is None: raise AssertionError("Couldn't parse receipts page")
                names = parsed_page.xpath("//div[contains(@class,'name_on_card')]/text()")
                return names[0] if len(names)>0 else ""
            except requests.exceptions.ConnectionError:
                print("!", end='')
                pass

    def _get_tender_type(self, payment) -> str:
        xform = {
            "VISA":"Visa",
            "MASTER_CARD":"MC",
            "AMERICAN_EXPRESS":"Amex",
            "DISCOVER": "Disc"
        }
        type = payment["tender"][0].get("card_brand", "")
        if type == "": type = payment["tender"][0].get("name", "?")
        if type in xform: type = xform[type]
        return type

    def _special_case_ixStxgstn56QI8jnJtcCtzMF(self, sale):
        mship = Membership()
        mship.sale = Sale(id=sale['id'])
        mship.membership_type = Membership.MT_REGULAR
        mship.ctrlid = "{}:1:1".format(sale['ctrlid'])
        mship.start_date = date(2014, 12, 12)
        mship.end_date = date(2015, 6, 11)
        mship.sale_price = 225.00
        self.upsert(mship)

    def _special_case_0JFN0loJ0kcy8DXCvuDVwwMF(self, sale):
        mship = Membership()
        mship.sale = Sale(id=sale['id'])
        mship.member = Member(id=19)  # Lookup by name would be better but I don't want to have names in the code.
        mship.membership_type = Membership.MT_WORKTRADE
        mship.ctrlid = "{}:1:1".format(sale['ctrlid'])
        mship.start_date = date(2015, 12, 1)
        mship.end_date = date(2015, 12, 31)
        mship.sale_price = 10.00
        self.upsert(mship)

    def _special_case_7cQ69ctaeYok1Ry3KOTFbyMF(self, sale):
        mship = Membership()
        mship.sale = Sale(id=sale['id'])
        mship.membership_type = Membership.MT_REGULAR
        mship.ctrlid = "{}:1:1".format(sale['ctrlid'])
        mship.start_date = date(2016, 4, 5)
        mship.end_date = date(2015, 4, 18)
        mship.sale_price = 25.00
        self.upsert(mship)


    SALES_TO_SKIP = [
        "A8CAHHFZZFBK3",            # $0, no items
        "8J4ZaFUnIU5e2NlEn2UkKQB",  # Cash sale, fully refunded. Customer did subsequent credit card sale.
        "U3dZYqFP1rKtjJImyYuNfvMF", # This was a 'Refill Soda Account' test, fully refunded.
        "CGvCOYS9VFEVgKlr6fP4KQB",  # Fully refunded. This was an accidental cash purchase. Redid it as credit.
    ]

    def _process_payments(self, payments):

        for payment in payments:

            # TODO: Clean out any existing sale & line items in case of refund, and then skip.
            # Refund sensing logic will be something like this:
            #    if len(payment.refunds)>0
            #      and payment.refunds[0].payment_id == payment.id
            #      and payment.refunds[0].type == "FULL"

            if payment['tender'][0]['type'] == "NO_SALE":
                continue

            if payment['id'] in self.SALES_TO_SKIP: continue

            if len(payment["tender"]) != 1:
                print("Code doesn't handle multiple tenders as in {}. Skipping.".format(payment['id']))
                continue

            sale = Sale()
            sale.sale_date = parse(payment["created_at"]).date()
            sale.payer_name = self.get_name_from_receipt(payment['receipt_url'])
            sale.payer_email = ""  # Annoyingly, not provided by Square.
            sale.payment_method = Sale.PAID_BY_SQUARE
            sale.method_detail = self._get_tender_type(payment)
            sale.total_paid_by_customer = Decimal(payment["tender"][0]["total_money"]["amount"]) / Decimal(100)
            sale.processing_fee = abs(Decimal(payment["processing_fee_money"]["amount"])) / Decimal(100)
            sale.ctrlid = "SQ:" + payment["id"]
            #sale.payer_notes = payment.get("notes", "").strip()

            if payment['id'] == "ixStxgstn56QI8jnJtcCtzMF":
                sale.payer_name = sale.payer_name.replace("M ", "MIKE ")

            django_sale = self.upsert(sale)

            if payment['id'] == "7cQ69ctaeYok1Ry3KOTFbyMF":
                # Person wanted to pay for two weeks while he was in town.
                # I added an item for this but don't like the way it worked out.
                # So I'm treating this as a special case.
                self._special_case_7cQ69ctaeYok1Ry3KOTFbyMF(django_sale)

            elif payment['id'] == "0JFN0loJ0kcy8DXCvuDVwwMF":
                # This is a work trade payment that was erroneously entered as a custom payment.
                # So we do this special processing to ingest it as a 1 month Work Trade membership.
                self._special_case_0JFN0loJ0kcy8DXCvuDVwwMF(django_sale)

            elif payment['id'] == "ixStxgstn56QI8jnJtcCtzMF":
                # This is a six month membership that was erroneously entered as a custom payment.
                # So we do this special processing to ingest it as a 6 month membership.
                self._special_case_ixStxgstn56QI8jnJtcCtzMF(django_sale)

            else:
                itemizations = payment['itemizations']
                self._process_itemizations(itemizations, django_sale)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # INIT & ABSTRACT METHODS
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def __init__(self):
        merchant_id = input("Square Merchant ID: ")
        rest_token = input("Square Token: ")
        if len(merchant_id) + len(rest_token) == 0:
            self.skip = True
        else:
            self.skip = False
            self.merchant_id = merchant_id
            self.rest_token = rest_token

    def fetch(self):

        get_headers = {
            'Authorization': "Bearer " + self.rest_token,
            'Accept': "application/json",
        }

        post_put_headers = {
            'Authorization': "Bearer " + self.rest_token,
            'Accept': "application/json",
            'Content-Type': "application/json",
        }

        payments_url = "https://connect.squareup.com/v1/{}/payments".format(self.merchant_id)

        window_start = date(2013, 12, 1)
        while window_start < date.today():
            window_start = window_start + relativedelta(months=+1)
            window_end = window_start + relativedelta(months=+1)
            get_data = {
                'begin_time': window_start.isoformat(),
                'end_time': window_end.isoformat(),
                'limit': str(200)  # Max allowed by Square
            }
            response = None
            while response is None:
                try:
                    response = self.squaresession.get(payments_url, params=get_data, headers=get_headers)
                except requests.exceptions.ConnectionError:
                    print("!", end='')

            payments = response.json()
            self._process_payments(payments)
        self._fetch_complete()