
# Standard
import logging
import os

# Third party
from django.contrib.auth.models import User
from nameparser import HumanName
from social.apps.django_app.default.models import UserSocialAuth
import lxml.html
import requests

# Local


__author__ = 'adrian'

# IMPORTANT: Check SERVER URL before commit. Don't commit test server.
SERVER = "http://www.xerocraft.org/"  # https is not available
ACTION_URL = SERVER+"actions.php"


class XerocraftScraper(object):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("xerocraft-django")
        self.session = requests.session()

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
        response = self.session.post(ACTION_URL, postdata)
        if response.text.find('<a href="./index.php?logout=true">[Logout?]</a>') == -1:
            self.logger.error("Could not log in %s", id)
            return False
        if response.text.find('>Administrator Page</a>') == -1:
            self.logger.warning("Less data will be collected since %s is not an administrator", id)
            # REVIEW: Should this return False? Probably not...
        return True

    def logout(self):
        response = self.session.get(SERVER+"index.php?logout=true")
        if response.text.find('<u>Sign In Options</u>') == -1:
            self.logger.error("Unexpected response from xerocraft.org logout.")

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
