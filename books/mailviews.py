
# Standard

# Third Party
from django.contrib.auth.models import User

# Local
from modelmailer.mailviews import MailView, register
from books.models import Donation, Sale, ReceivableInvoice

TREASURER = "Xerocraft Treasurer <treasurer@xerocraft.org>"
XIS = "Xerocraft Systems <xis@xerocraft.org>"
BCCS = [TREASURER, XIS]
#BCCS = [XIS]  # Don't bother Treasurer when testing.

def _email(trans_desc_str: str, email_str: str, acct: User):
    email = None
    if email_str != "":
        email = email_str
    elif acct is not None and acct.email != "":
        email = acct.email
    if email is None:
        raise RuntimeWarning("Cannot determine email addr for: %s" % trans_desc_str)
    return email


def _first_name(name: str, acct: User):
    first_name = None
    # TODO: Could use person name parser here to get first name from "name"
    if acct is not None:
        first_name = acct.first_name
        if first_name == "":
            first_name = None
    return first_name


def _full_name(name: str, acct: User):
    full_name = None
    if name != "":
        full_name = name
    elif acct is not None:
        full_name = "{} {}".format(acct.first_name, acct.last_name).strip()
        if full_name == "":
            full_name = None
    return full_name


# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

@register(Donation)
class PhysicalDonationMailView(MailView):

    def get_email_spec(self, donation: Donation) -> dict:
        acct = donation.donator_acct

        donor_email = _email(str(donation), donation.donator_email, acct)
        first_name = _first_name(donation.donator_name, acct)
        full_name = _full_name(donation.donator_name, acct)

        spec = {
            'sender': "Xerocraft Systems <xis@xerocraft.org>",
            'recipients': [donor_email],
            'subject': "Receipt for Physical Donation to Xerocraft",
            'bccs': BCCS,
            'template': "books/email-phys-donation",  # Name without .html or .txt extension
            'parameters': {
                'first_name': first_name,
                'full_name': full_name,
                'donation': donation,
                'items': donation.donateditem_set.all(),
            },
            'info-for-log':"Receipt for physical donation #{} sent to {}.".format(donation.pk, donor_email)
        }
        return spec


# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

# Following class is registered to "Sale" but it only emails a receipt for the cash donation portion of a sale.
@register(Sale)
class CashDonationMailView(MailView):

    def get_email_spec(self, sale: Sale) -> dict:
        acct = sale.payer_acct

        donor_email = _email(str(sale), sale.payer_email, acct)
        first_name = _first_name(sale.payer_name, acct)
        full_name = _full_name(sale.payer_name, acct)

        items = sale.monetarydonation_set.all()
        for item in items:
            item.deductible = item.amount
            if item.reward is not None:
                item.deductible -= item.reward.fair_mkt_value

        spec = {
            'sender': "Xerocraft Systems <xis@xerocraft.org>",
            'recipients': [donor_email],
            'subject': "Receipt for Cash Donation to Xerocraft",
            'bccs': BCCS,
            'template': "books/email-cash-donation",  # Name without .html or .txt extension
            'parameters': {
                'first_name': first_name,
                'full_name': full_name,
                'sale': sale,
                'items': items,
            },
            'info-for-log':"Receipt for monetary donation in sale #{} sent to {}.".format(sale.pk, donor_email)
        }
        return spec


# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

@register(ReceivableInvoice)
class ReceivableInvoiceMailView(MailView):

    def get_email_spec(self, rinv: ReceivableInvoice) -> dict:
        acct = rinv.user
        ent = rinv.entity
        ent_email = "" if ent is None else ent.email
        ent_name = "" if ent is None else ent.name

        email = _email(str(rinv), ent_email, acct)
        full_name = _full_name(ent_name, acct)

        items2 = []
        link_names = rinv.link_names_of_relevant_children()
        for link_name in link_names:
            children = getattr(rinv, link_name).all()
            for child in children:
                items2.append(child)

        spec = {
            'sender': "Xerocraft Systems <xis@xerocraft.org>",
            'recipients': [email],
            'subject': "Invoice {}, Payable to Xerocraft".format(rinv.invoice_number_str),
            'bccs': BCCS,
            'template': "books/email-receivable-invoice",  # Name without .html or .txt extension
            'parameters': {
                'full_name': full_name,
                'invoice': rinv,
                'notes': rinv.receivableinvoicenote_set.all(),
                'items': rinv.receivableinvoicelineitem_set.all(),
                'items2': items2,
            },
            'info-for-log':"Receivable Invoice #{} sent to {}.".format(rinv.pk, email)
        }
        return spec
