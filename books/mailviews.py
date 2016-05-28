
# Standard

# Third Party

# Local
from modelmailer.mailviews import MailView, register
from .models import Donation

TREASURER = "Xerocraft Treasurer <treasurer@xerocraft.org>"


@register(Donation)
class DonationMailView(MailView):

    def get_email_spec(self, target: Donation) -> dict:
        donation = target
        acct = donation.donator_acct

        donor_email = None
        if donation.donator_email != "":
            donor_email = donation.donator_email
        elif acct is not None and acct.email != "":
            donor_email = acct.email

        if donor_email is None:
            raise RuntimeWarning("Cannot determine donor's email addr for: %s", target)

        first_name = None
        if acct is not None:
            first_name = acct.first_name
            if first_name == "":
                first_name = None

        full_name = None
        if donation.donator_name != "":
            full_name = donation.donator_name
        elif acct is not None:
            full_name = "{} {}".format(acct.first_name, acct.last_name).strip()
            if full_name == "":
                full_name = None

        spec = {
            'sender': "Xerocraft Systems <xis@xerocraft.org>",
            'recipients': [TREASURER, donor_email],
            'subject': "Receipt for Donation to Xerocraft",
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



