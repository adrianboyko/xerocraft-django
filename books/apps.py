# Standard
import json
import logging

# Third Party
from django.apps import AppConfig
from django.conf import settings

import requests

# Local

__author__ = 'Adrian'

_logger = logging.getLogger("books")

SQUAREUP_LOCATION_ID = settings.XEROPS_BOOKS_CONFIG['SQUAREUP_LOCATION_ID']
SQUAREUP_APIV1_TOKEN = settings.XEROPS_BOOKS_CONFIG['SQUAREUP_APIV1_TOKEN']


class BooksAppConfig(AppConfig):
    name = 'books'
    verbose_name = 'Books'

    def activate_squareup_webhooks(self):
        if SQUAREUP_APIV1_TOKEN is None or SQUAREUP_APIV1_TOKEN is None:
            _logger.info("SquareUp API V1 Token and/or Location ID not set in environment.")
            return
        try:
            put_headers = {
                'Authorization': "Bearer " + SQUAREUP_APIV1_TOKEN,
                'Accept': "application/json",
                'Content-Type': "application/json",
            }
            url = "https://connect.squareup.com/v1/{}/webhooks".format(SQUAREUP_LOCATION_ID)
            payload = ["PAYMENT_UPDATED"]
            response = requests.put(url, data=json.dumps(payload), headers=put_headers)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            _logger.error("Couldn't register SquareUp webhook.")

    def ready(self):
        import books.signals.handlers
        self.activate_squareup_webhooks()

