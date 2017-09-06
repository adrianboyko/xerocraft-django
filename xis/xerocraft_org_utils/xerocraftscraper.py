
# Standard
import logging
import os

# Third party
from django.conf import settings
import requests

# Local


__author__ = 'adrian'


class XerocraftScraper(object):

    SERVER_DEV = "https://www.xerocraft.org/kfritz/"
    SERVER_PROD = "https://www.xerocraft.org/"

    def __init__(self, server_override=None):
        super().__init__()
        self.logger = logging.getLogger("xis")
        self.session = requests.session()
        if server_override is not None:
            self.server = server_override
        else:
            self.server = XerocraftScraper.SERVER_DEV if settings.ISDEVHOST else XerocraftScraper.SERVER_PROD
        self.action_url = self.server + "actions.php"

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def login(self):
        id = os.environ['XEROCRAFT_WEBSITE_ADMIN_ID']
        pw = os.environ['XEROCRAFT_WEBSITE_ADMIN_PW']
        postdata = {
            'SignInUsername': id,
            'SignInPassword': pw,
            'action': 'signin',
            'ax': 'n',
            'q': '',
        }
        response = self.session.post(self.action_url, postdata)
        if response.text.find('<a href="./index.php?logout=true">[Logout?]</a>') == -1:
            self.logger.error("Could not log in %s", id)
            return False
        if response.text.find('>Administrator Page</a>') == -1:
            self.logger.warning("Less data will be collected since %s is not an administrator", id)
            # REVIEW: Should this return False? Probably not...
        return True

    def logout(self):
        response = self.session.get(self.server+"index.php?logout=true")
        if response.text.find('<u>Sign In Options</u>') == -1:
            self.logger.error("Unexpected response from xerocraft.org logout.")

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
