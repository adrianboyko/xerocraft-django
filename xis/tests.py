
# Standard
import os

# Third Party
from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command

# Local
from xis.xerocraft_org_utils.paypalscraper import PaypalScraper


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TestAuthentication(TestCase):

    def test_xerocraft_org_auth(self):
        # Note: Since test DB is empty, authentication uses AccountScraper.
        # User.objects.count() is used to check for successful scraping.
        self.assertEqual(User.objects.count(), 0)
        id = os.environ['XEROCRAFT_WEBSITE_ADMIN_ID']
        pw = os.environ['XEROCRAFT_WEBSITE_ADMIN_PW']
        user = authenticate(username=id, password=pw)
        self.assertIsNotNone(user)
        self.assertEqual(User.objects.count(), 1)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TestPaypalScraper(TestCase):

    def test_it(self):
        scraper = PaypalScraper()
        ids = scraper.scrape_agreement_ids()
        # The following assertion assumes that xerocraft.org has agreement ids to scrape.
        self.assertGreater(len(ids), 0)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TestManagementCommands(TestCase):

    def test_scrapecheckins_command(self):
        call_command('scrapecheckins')
        # Since we're now running the test against xerocraft.org test system,
        # the following assertion is rarely true. Removing it.
        # self.assertGreater(User.objects.count(), 0)

    def test_scrapememberlist_command(self):
        call_command('scrapememberlist')
        self.assertGreater(User.objects.count(), 0)
