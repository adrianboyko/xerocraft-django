
# Standard
import logging

# Third Party
import requests
from django.contrib.auth.backends import ModelBackend
from django.conf import settings

# Local
from xis.xerocraft_org_utils.accountscraper import AccountScraper


class XerocraftBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        # TODO: This would be a lot better/simpler if xerocraft.org's actions.php would offer
        # action:authenticate, SignInIdentifier:<email or username>, SignInPassword:<password>
        # that returned {auth:"yes", username:<username>, email:<email>, name:<name>} or {auth:"no"}

        identifier = username  # Given "username" is actually a more generic identifier.
        session = requests.session()
        logger = logging.getLogger("xis")
        server = "https://www.xerocraft.org/kfritz/" if settings.ISDEVHOST else "https://www.xerocraft.org/"
        action_url = server+"actions.php"

        # Try logging in to xerocraft.org to authenticate given username and password:
        postdata = {'SignInUsername':identifier, 'SignInPassword':password, 'action':'signin'}
        response = session.post(action_url, postdata)
        if response.text.find('<a href="./index.php?logout=true">[Logout?]</a>') == -1:
            # xerocraft.org said there's no such identifier/password.
            return None

        # At this point we know that the id/pw authenticated on remote xerocraft.
        # So we use Scraper to scrape it which will result in new or updated local account.
        try:  # to parse out the usernum
            usernum_seek = 'profiles.php?id='
            usernum_start = response.text.find(usernum_seek)
            if usernum_start == -1: raise AssertionError("Couldn't find start of usernum")
            usernum_end = response.text.find('"', usernum_start)
            if usernum_end == -1: raise AssertionError("Couldn't find end of usernum")
            usernum = response.text[usernum_start+len(usernum_seek):usernum_end]
            if not usernum.isdigit(): raise AssertionError("Didn't find a numeric usernum")
        except (AssertionError, requests.HTTPError) as err:
            logger.error(str(err))
            return None

        # Reuse the Scraper's logic to create a user for this usernum.
        scraper = AccountScraper()
        user = scraper.scrape_one_account(usernum)

        assert(user is not None)
        # Scraper doesn't have access to pws, so they need to be synched by this authenticator.
        password_before = user.password
        user.set_password(password)
        if password_before != user.password:
            user.save()
            logger.info("Updated password for %s.", user.username)

        # Xerocraft.org SERVER maintains a "logged in status" for display
        # to other users. So explicitly log out to prevent that.
        response = session.get(server+"index.php?logout=true")
        if response.text.find('<u>Sign In Options</u>') == -1:
            logger.error("Unexpected response from xerocraft.org logout.")

        return user
