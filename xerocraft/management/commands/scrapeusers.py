from django.core.management.base import BaseCommand, CommandError
from django.template import Context
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from social.apps.django_app.default.models import UserSocialAuth
from nameparser import HumanName
import logging
import requests
import os
import sys
import lxml.html


__author__ = 'adrian'

# IMPORTANT: Check SERVER URL before commit. Don't commit test server.
SERVER = "http://www.xerocraft.org/" # https is not available
ACTION_URL = SERVER+"actions.php"

EMAIL_KEY = "Email address"
PHONE_KEY = "Phone number"
USERNUM_KEY = "User number"
USERNAME_KEY = "User name"
REALNAME_KEY = "Name"
FIRSTNAME_KEY = "First Name"  # Infered from real name using "nameparser"
LASTNAME_KEY = "Last Name"  # Infered from real name using "nameparser"
SINCE_KEY = "Online-member since"
PARTICIPATION_KEY = "Participation Rank"
DJANGO_USERNAME_KEY = "Django user name"  # Constructed by _djangofy_username()
ROLE_KEY = "Role at Xerocraft"
PROVIDER = "xerocraft.org"

UNINTERESTING_KEYS = [PARTICIPATION_KEY, SINCE_KEY, ROLE_KEY]


class Command(BaseCommand):

    help = "Scrapes xerocraft.org/profiles.php and creates corresponding accounts on this website, if not already created."
    logger = logging.getLogger("xerocraft-django")
    session = requests.session()
    # In any given run, we expect to see the following keys.
    # If we don't, the website has changed or something else has gone wrong.
    unseen_keys = [
        EMAIL_KEY, PHONE_KEY, USERNUM_KEY, USERNAME_KEY,
        REALNAME_KEY, FIRSTNAME_KEY, LASTNAME_KEY,
        SINCE_KEY, PARTICIPATION_KEY, ROLE_KEY]

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def _djangofy_username(username):
        newname = ""
        for c in username:
            if c.isalnum() or c in "_@+.-": newname += c
            else: newname += "_"
        return newname

    @staticmethod
    def _print_attrs(attrs):
        for k,v in sorted(attrs.items()):
            if k in UNINTERESTING_KEYS: continue
            print("   %s: %s" % (k,v))
        print()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

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

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def process_account_diffs(self, user_social_auth, attrs):
        user = user_social_auth.user

        if user_social_auth.extra_data != attrs:
            user_social_auth.extra_data = attrs
            user_social_auth.save()
            self.logger.info("Updated extra data for %s", user.username)

    def create_account(self, attrs):
        try:
            pw = User.objects.make_random_password()
            new_user = User.objects.create(
                username=attrs[DJANGO_USERNAME_KEY],
                first_name=attrs.get(FIRSTNAME_KEY,""),
                last_name=attrs.get(LASTNAME_KEY,""),
                email=attrs.get(EMAIL_KEY,""),
                is_superuser=False,
                is_staff=False,
                is_active=True,
                password=pw,
            )
            new_usa = UserSocialAuth.objects.create(
                user=new_user,
                provider=PROVIDER,
                uid=attrs[USERNUM_KEY],
                extra_data=attrs,
            )
        except:
            if new_user is not None: new_user.delete()
            if new_usa is not None: new_usa.delete()
            raise

        self.logger.info(
            "Scraped a new user: %s --> %s",
            attrs[USERNAME_KEY], attrs[DJANGO_USERNAME_KEY])

        return new_user

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def scrape_profile(self, user_num):

        # Get the profile corresponding to user_num
        response = self.session.post(ACTION_URL, data={"action": "ViewProfile", "id": user_num, "ax": "y"})
        profile_parsed = lxml.html.fromstring(response.text)
        if profile_parsed is None: raise AssertionError("Couldn't parse profile for usernum"+user_num)

        # Pull out interesting info
        attr_names = profile_parsed.xpath("//div[@id='pp_upper_right']/ul[@class='left']/li/text()")
        attr_vals  = profile_parsed.xpath("//div[@id='pp_upper_right']/ul[@class='right']/li/text()")
        username = profile_parsed.xpath("//div[@id='pp_username']//h1/text()")[0]

        # Make a dictionary of attributes and massage/infer values, as required.
        attrs = dict(zip(attr_names, attr_vals))
        attrs[USERNUM_KEY] = user_num
        attrs[USERNAME_KEY] = username
        attrs[DJANGO_USERNAME_KEY] = Command._djangofy_username(username)
        if REALNAME_KEY in attrs:
            attrs[REALNAME_KEY] = attrs[REALNAME_KEY].replace(" (Admin)", "")
            name = HumanName(attrs[REALNAME_KEY])
            attrs[FIRSTNAME_KEY] = name.first
            attrs[LASTNAME_KEY] = name.last

        if self.unseen_keys:
            for key in attrs.keys():
                if key in self.unseen_keys:
                    self.unseen_keys.remove(key)

        # There's a bug in xerocraft.org that gives a large percentage of members the current date
        # as their "member since" date. This looks like data changing every day. Since it's not
        # used for anything here on xerocraft-django, I'm going to throw it away.
        if SINCE_KEY in attrs: del attrs[SINCE_KEY]

        # Do something with the scraped attrs
        try:
            usa = UserSocialAuth.objects.get(provider=PROVIDER, uid=attrs[USERNUM_KEY])
            self.process_account_diffs(usa, attrs)
            return usa.user

        except UserSocialAuth.DoesNotExist:
            return self.create_account(attrs)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def add_manually_scraped():
        """
            Some accounts were manually scraped before the scraper was created.
            This adds UserSocialAuths for them. This code can be deleted after
            initial deployment of scraping to production.
        """
        items = [
            ( 102, 1), (  88, 2), (255, 3), ( 409, 4), ( 115, 5), ( 123, 6),
            ( 117, 7), ( 831, 8), (629, 9), ( 611,11), ( 148,12), ( 256,13),
            (  85,14), ( 618,15), (266,16), ( 172,17), ( 274,18), (  94,19),
            (1328,23), ( 152,24), (154,26), (1235,27), ( 654,28), (  97,29),
            ( 769,30), (1237,32), (485,33), ( 151,38), (1417,40), (1418,41),
            (1472,42), (1286,43), (100,45)
        ]

        for (php_id, django_id) in items:
            django_user = User.objects.get(id=django_id)
            try:
                UserSocialAuth.objects.create(
                    user=django_user,
                    provider=PROVIDER,
                    uid=php_id,
                )
            except IntegrityError:
                pass  # This just means that a previous run already created it.

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def handle(self, *args, **options):
        logger = logging.getLogger("members")

        Command.add_manually_scraped()

        if not self.login():
            # Problem is already logged in self.login
            return

        page = 1  # IMPORTANT: Set to 1 before commit!
        while True:
            response = self.session.post(ACTION_URL,data={"action": "ViewMembersList", "p": page})
            if response.text.find("There are no users to display") >= 0:
                return

            page_parsed = lxml.html.fromstring(response.text)
            if page_parsed is None: raise AssertionError("Couldn't parse members page")
            user_nums = page_parsed.xpath("//div[contains(@class,'member')]/a/@targetmember")
            for user_num in user_nums:
                try:
                    self.scrape_profile(user_num)
                except:
                    # Failure on a particular profile doesn't mean we give up on the rest.
                    # Just log the error and carry on with the rest.
                    # REVIEW: Might want to give up if there are "too many" errors.
                    e = sys.exc_info()[0]
                    logger.error("Failure while working on profile %s: %s", user_num, str(e))

            page += 1
            #if page > 1: break # IMPORTANT: Remove or disable following line before commit!

        self.logout()
        for key in self.unseen_keys:
            self.logger.warning("Did not encounter '%s' key.", key)