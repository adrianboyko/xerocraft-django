
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
from xis.xerocraft_org_utils.xerocraftscraper import XerocraftScraper

__author__ = 'adrian'

# IMPORTANT: Check SERVER URL before commit. Don't commit test server.
SERVER = "http://www.xerocraft.org/"  # https is not available
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


class AccountScraper(XerocraftScraper):

    @staticmethod
    def djangofy_username(username):
        username = username.strip()  # Kyle has verified that xerocraft.org database has some untrimmed usernames.
        newname = ""
        for c in username:
            if c.isalnum() or c in "_@+.-":
                newname += c
            else:
                newname += "_"
        return newname

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def process_account_diffs(self, user_social_auth, attrs):

        # Changeables is a list of (key name in attrs, field name in Django model) tuples.
        # These are the fields we'll check for changes.
        changeables = [
            (DJANGO_USERNAME_KEY, "username"),
            (FIRSTNAME_KEY,       "first_name"),
            (LASTNAME_KEY,        "last_name"),
            (EMAIL_KEY,           "email"),
        ]

        user = user_social_auth.user
        user_changed = False
        for key, fieldname in changeables:
            oldval = getattr(user, fieldname) if hasattr(user,fieldname) else ""
            newval = attrs[key] if key in attrs else ""
            if newval in ["", None]: continue  # Don't want scraper to clear values.
            if oldval != newval:
                printable_oldval = oldval if oldval != "" else None
                self.logger.info("Updating %s, %s > %s", fieldname, printable_oldval, newval)
                setattr(user, fieldname, newval)
                user_changed = True

        if user_changed:
            user.save()

        extra_changed = False
        for key, val in attrs.items():
            if val in ["", None]: continue
            user_social_auth.extra_data[key] = val
            extra_changed = True
        if extra_changed:
            user_social_auth.save()

    def create_account(self, attrs):

        new_user = User.objects.create(
            username=attrs[DJANGO_USERNAME_KEY],
            first_name=attrs.get(FIRSTNAME_KEY, ""),
            last_name=attrs.get(LASTNAME_KEY, ""),
            email=attrs.get(EMAIL_KEY, ""),
            is_superuser=False,
            is_staff=False,
            is_active=True,
            password=User.objects.make_random_password(),
        )

        new_usa = UserSocialAuth.objects.create(
            user=new_user,
            provider=PROVIDER,
            uid=attrs[USERNUM_KEY],
            extra_data=attrs,
        )

        self.logger.info(
            "Scraped a new user: %s > %s",
            attrs[USERNAME_KEY], attrs[DJANGO_USERNAME_KEY])

        return new_user

    def process_attrs(self, attrs):
        try:
            usa = UserSocialAuth.objects.get(provider=PROVIDER, uid=attrs[USERNUM_KEY])
            self.process_account_diffs(usa, attrs)
            return usa.user
        except UserSocialAuth.DoesNotExist:
            return self.create_account(attrs)

    def scrape_profile(self, user_num):

        # Get the profile corresponding to user_num
        post_data = {"action": "ViewProfile", "id": user_num, "ax": "y"}
        response = self.session.post(ACTION_URL, data=post_data)
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
        attrs[DJANGO_USERNAME_KEY] = self.djangofy_username(username)
        if REALNAME_KEY in attrs:
            attrs[REALNAME_KEY] = attrs[REALNAME_KEY].replace(" (Admin)", "")
            name = HumanName(attrs[REALNAME_KEY])
            attrs[FIRSTNAME_KEY] = name.first
            attrs[LASTNAME_KEY] = name.last

        # Do something with the scraped attrs
        result = self.process_attrs(attrs)
        result.scraped_attrs = attrs  # The caller might want the scraped attrs.
        return result

