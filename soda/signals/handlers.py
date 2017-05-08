
# Standard

# Third-party
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

# Local
from ..models import VendLog, VendingMachineBin

__author__ = 'Adrian'


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# VENDLOG
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@receiver(post_save, sender=VendLog)
def vend_it(sender, **kwargs):
    if kwargs.get('created', True):
        log_entry = kwargs.get('instance')  # type: VendLog
        log_entry.product.vend()

