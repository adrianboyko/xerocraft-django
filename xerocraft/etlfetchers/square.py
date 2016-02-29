from xerocraft.etlfetchers.abstractfetcher import AbstractFetcher
from members.models import PaidMembership
from datetime import date
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import requests
import lxml
import lxml.html


# Note: This class must be named Fetcher in order for dynamic load to find it.
class Fetcher(AbstractFetcher):

    session = requests.Session()

    uninteresting = [
        "Donation",
        "Workshop Fee",
        "Custom Amount",  # I believe this is a donation.
        "Refill Soda Account",
        "Holiday Gift Card (6 months)",
        "Holiday Gift Card (3 months)",
        "Bumper Sticker",
        "Medium Sticker",
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
            elif item['name'] in self.WORK_TRADE_ITEMS:
                months = 1
                short_item_code = "WT"
                membership_type = PaidMembership.MT_WORKTRADE
            else:
                print("Didn't recognize item name: "+item['name'])
                continue

            month = self.month_in_str(item['name'])

            for modifier in item["modifiers"]:
                lmod = modifier["name"].lower()
                if lmod == "just myself": family_count = 0
                elif lmod == "1 add'l family member":  family_count = 1
                elif lmod == "2 add'l family members": family_count = 2
                elif lmod == "3 add'l family members": family_count = 3
                elif lmod == "4 add'l family members": family_count = 4
                elif lmod == "5 add'l family members": family_count = 5
                if membership_type == PaidMembership.MT_WORKTRADE and month is None:
                    month = self.month_in_str(lmod)

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
                pm.payer_notes = item.get("notes", "").strip()
                pm.payment_date = payment_date
                pm.start_date = pm.payment_date
                if pm.membership_type == PaidMembership.MT_WORKTRADE:
                    pm.start_date = pm.start_date.replace(day=1)  # WT always starts on the 1st.
                    if month is not None:  # Hopefully, the buyer specified the month.
                        pm.start_date = pm.start_date.replace(month=month)
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
            payment_date = parse(payment["created_at"]).date()
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
        if merchant_id == "skip": return

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
            response = None
            while response is None:
                try:
                    response = self.session.get(payments_url, params=get_data, headers=get_headers)
                except ConnectionError:
                    print("!", end='')

            payments = response.json()
            for pm in self.gen_from_payment(payments):
                yield pm