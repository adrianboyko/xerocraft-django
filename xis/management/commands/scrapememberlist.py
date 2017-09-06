import sys

import lxml.html
from django.core.management.base import BaseCommand

from xis.xerocraft_org_utils.accountscraper import *

__author__ = 'adrian'


class Command(AccountScraper, BaseCommand):

    help = "Scrapes xerocraft.org/profiles.php and creates corresponding accounts on this website, if not already created."

    # In any given run, we expect to see the following keys.
    # If we don't, the website has changed or something else has gone wrong.
    unseen_keys = [
        EMAIL_KEY, PHONE_KEY, USERNUM_KEY, USERNAME_KEY,
        REALNAME_KEY, FIRSTNAME_KEY, LASTNAME_KEY,
        SINCE_KEY, PARTICIPATION_KEY, ROLE_KEY]

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def handle(self, *args, **options):

        if not self.login():
            # Problem is already logged in self.login
            return

        page = 1  # IMPORTANT: Set to 1 before commit!
        while True:
            post_data = {"action": "ViewMembersList", "p": page}
            response = self.session.post(self.action_url, data=post_data)
            if response.text.find("There are no users to display") >= 0:
                return

            page_parsed = lxml.html.fromstring(response.text)
            if page_parsed is None: raise AssertionError("Couldn't parse members page")
            user_nums = page_parsed.xpath("//div[contains(@class,'member')]/a/@targetmember")
            for user_num in user_nums:
                try:
                    scraped_user = self.scrape_profile(user_num)
                    if self.unseen_keys:
                        for key in scraped_user.scraped_attrs.keys():  # scraped_attrs is added by scrape_profile
                            if key in self.unseen_keys:
                                self.unseen_keys.remove(key)
                except:
                    # Failure on a particular profile doesn't mean we give up on the rest.
                    # Just log the error and carry on with the rest.
                    # REVIEW: Might want to give up if there are "too many" errors.
                    e = sys.exc_info()[0]
                    self.logger.error("Failure while working on profile %s: %s", user_num, str(e))

            page += 1
            #if page > 1: break # IMPORTANT: Remove or disable following line before commit!

        self.logout()
        for key in self.unseen_keys:
            self.logger.warning("Did not encounter '%s' key.", key)