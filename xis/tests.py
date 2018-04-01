
# Standard
import os

# Third Party
from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command

# Local
from xis.xerocraft_org_utils.paypalscraper import PaypalScraper
from xis.xerocraft_org_utils.accountscraper import AccountScraper
from xis.xerocraft_org_utils.xerocraftscraper import XerocraftScraper


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TestAuthentication(TestCase):

    def test_xerocraft_org_auth(self):
        id = os.environ['XEROCRAFT_WEBSITE_ADMIN_ID']
        pw = os.environ['XEROCRAFT_WEBSITE_ADMIN_PW']

        # Note: Since test DB is empty, authentication uses AccountScraper.
        # User.objects.count() is used to check for successful scraping.
        self.assertEqual(User.objects.count(), 0)
        user = authenticate(username=id, password=pw)
        self.assertIsNotNone(user)
        self.assertEqual(User.objects.count(), 1)

        # Now that test DB is no longer empty, a subsequent authentication
        # of the same user should not create a new User object.
        user = authenticate(username=id, password=pw)
        self.assertIsNotNone(user)
        self.assertEqual(User.objects.count(), 1)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# TEMPORARILY REMOVED! DOES NOT TEST FUNCTIONALITY OF PRODUCTION SERVER.
# class TestPaypalScraper(TestCase):
#
#     def test_it(self):
#         scraper = PaypalScraper()
#         ids = scraper.scrape_agreement_ids()
#         # The following assertion assumes that xerocraft.org has agreement ids to scrape.
#         self.assertGreater(len(ids), 0)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Test_ScrapeMemberList(TestCase):

    def test_scrapememberlist_command(self):
        # NOTE: This will "scrape" the test server.
        call_command('scrapememberlist')
        self.assertGreater(User.objects.count(), 0)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TestAccountScraper(TestCase):

    def test_single_user(self):
        scraper = AccountScraper()
        # This test depends on the current contents of the xerocraft.org test system.
        u = scraper.scrape_one_account(5)  # type: User
        self.assertEqual(u.first_name, "Kyle")

    def test_all_users(self):
        # NOTE: This is INTENTIONALLY "scraping" the PRODUCTION server
        scraper = AccountScraper(XerocraftScraper.SERVER_PROD)
        initial_count = User.objects.count()

        # An initial scrape should produce many users.
        scraper.scrape_all_accounts()
        after_scrape1_count = User.objects.count()
        self.assertGreater(after_scrape1_count, initial_count)

        # A subsequent scrape shouldn't produce any more users
        # (unless we were unlucky and somebody signed up during our test)
        scraper.scrape_all_accounts()
        after_scrape2_count = User.objects.count()
        self.assertEqual(after_scrape1_count, after_scrape2_count)
