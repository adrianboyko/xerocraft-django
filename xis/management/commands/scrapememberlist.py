import sys

import lxml.html
from django.core.management.base import BaseCommand

from xis.xerocraft_org_utils.accountscraper import *

__author__ = 'adrian'


class Command(BaseCommand):

    help = "Scrapes xerocraft.org/profiles.php and creates corresponding accounts on this website, if not already created."

    # In any given run, we expect to see the following keys.
    # If we don't, the website has changed or something else has gone wrong.
    unseen_keys = [
        EMAIL_KEY, PHONE_KEY, USERNUM_KEY, USERNAME_KEY,
        REALNAME_KEY, FIRSTNAME_KEY, LASTNAME_KEY
    ]

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def handle(self, *args, **options):
        scraper = AccountScraper()
        scraper.scrape_all_accounts()