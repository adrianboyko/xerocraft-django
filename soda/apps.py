# Standard
import logging

# Third-party
from django.apps import AppConfig

# Local

__author__ = 'Adrian'

_logger = logging.getLogger("soda")


class SodaConfig(AppConfig):
    name = 'soda'

    def ready(self):
        import soda.signals.handlers