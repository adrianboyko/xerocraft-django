
# Standard
from typing import Optional
from sys import exc_info

# Third party
from django.contrib.auth.models import User
from nameparser import HumanName
from members.models import ExternalId
import requests

# Local
from .xerocraftscraper import XerocraftScraper

__author__ = 'adrian'

EMAIL_KEY = "Email"
PHONE_KEY = "Phone"
USERNUM_KEY = "AutoInc"
USERNAME_KEY = "Username"
REALNAME_KEY = "Name"
MINOR_KEY = "Minor"
BANNED_KEY = "Banned"

FIRSTNAME_KEY = "FName"  # Infered from real name using "nameparser"
LASTNAME_KEY = "LName"  # Infered from real name using "nameparser"
DJANGO_USERNAME_KEY = "Django user name"  # Constructed by _djangofy_username()
ADULT_KEY = "IsAdult"

PROVIDER = "xerocraft.org"


class AccountScraper(XerocraftScraper):

    def __init__(self, server_override=None):
        super().__init__(server_override)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _process_account_diffs(self, ext_id_rec, attrs):

        # Changeables is a list of (key name in attrs, field name in Django model) tuples.
        # These are the fields we'll check for changes.
        changeables = [
            (DJANGO_USERNAME_KEY, "username"),
            (FIRSTNAME_KEY,       "first_name"),
            (LASTNAME_KEY,        "last_name"),
            (EMAIL_KEY,           "email"),
        ]

        user = ext_id_rec.user  # type: User
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

    def _create_account(self, attrs) -> User:

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

        new_extidrec = ExternalId.objects.create(
            user=new_user,
            provider=PROVIDER,
            uid=attrs[USERNUM_KEY],
            extra_data="",  # Will probably be removing this field.
        )

        self.logger.info(
            "Scraped a new user: %s > %s",
            attrs[USERNAME_KEY], attrs[DJANGO_USERNAME_KEY])

        return new_user

    def _process_attrs(self, attrs) -> User:
        try:
            extidrec = ExternalId.objects.get(provider=PROVIDER, uid=attrs[USERNUM_KEY])
            self._process_account_diffs(extidrec, attrs)
            return extidrec.user
        except ExternalId.DoesNotExist:
            return self._create_account(attrs)

    def scrape_one_account(self, user_num:int) -> User:
        post_data = {
            "XSC": XerocraftScraper.get_token(),
            "ID": user_num
        }
        return self._scrape(post_data)

    def scrape_all_accounts(self) -> None:
        post_data = {
            "XSC": XerocraftScraper.get_token(),
        }
        self._scrape(post_data)

    def _scrape(self, post_data) -> Optional[User]:  # REVIEW: This should be a generator instead?

        # I couldn't convince the other team not to obfuscate the resource name, so it's "JSON.php"
        response = requests.post(self.server+"JSON.php", data=post_data)
        result = None  # type: Optional[User]
        for attrs in response.json():

            try:
                uname = attrs[USERNAME_KEY]
                deleted = uname.startswith("DELETED:")
                empty = len(uname.strip()) == 0
                if deleted or empty: continue

                attrs[DJANGO_USERNAME_KEY] = self.djangofy_username(attrs[USERNAME_KEY])
                if REALNAME_KEY in attrs:
                    attrs[REALNAME_KEY] = attrs[REALNAME_KEY].replace(" (Admin)", "")
                    name = HumanName(attrs[REALNAME_KEY])
                    attrs[FIRSTNAME_KEY] = name.first
                    attrs[LASTNAME_KEY] = name.last
                    attrs[ADULT_KEY] = True if attrs[MINOR_KEY]=="1" else False
                result = self._process_attrs(attrs)
                result.scraped_attrs = attrs  # The caller might want the scraped attrs.

            except Exception as e:
                # Failure on a particular profile doesn't mean we give up on the rest.
                # Just log the error and carry on with the rest.
                # REVIEW: Might want to give up if there are "too many" errors.
                #e = exc_info()[0]
                self.logger.error("Failure while working on %s: %s", str(attrs), str(e))

        return result  # The return value is the LAST user scraped.

