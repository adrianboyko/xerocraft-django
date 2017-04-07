# Standard
import logging

# Third Party
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Local

__author__ = 'Adrian'

logger = logging.getLogger("bezewy-ops")


