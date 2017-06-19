
# Standard

# Third Party
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Local
from books.models import Sale, MonetaryDonation, Campaign

__author__ = 'Adrian'


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# SALE
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# TODO: Attempt to auto-link based on name/email in sale. Only for WePay, 2Checkout, Square?
@receiver(pre_save, sender=Sale)
def link_sale_to_user(sender, **kwargs):
    if kwargs.get('created', True):
        sale = kwargs.get('instance')
        if not sale.protected:
            sale.link_to_user()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# MONETARY DONATION
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@receiver(pre_save, sender=MonetaryDonation)
def link_donation_to_campaign(sender, **kwargs):
    donation = kwargs.get('instance')  # type: MonetaryDonation
    try:
        if donation.earmark.campaign_as_revenue is not None:
            # This is a denormalization. See comments on model.
            donation.campaign = donation.earmark.campaign_as_revenue
    except Campaign.DoesNotExist:
        pass

