from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from books.models import Sale

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


