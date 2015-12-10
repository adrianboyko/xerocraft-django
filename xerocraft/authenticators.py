import requests
import logging
import lxml.html
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

# TODO: Add case-insensitive index to User.username for performance.
# TODO: Add code somewhere to ensure that email addresses for users are unique.


# NOTE! In code below, "identifier" means "username or email address".as
def _get_local_user(identifier):
    if identifier.isspace() or len(identifier) == 0:
        return None
    try:
        user = User.objects.get(username__iexact=identifier)
        return user
    except User.DoesNotExist:
        pass
    try:
        user = User.objects.get(email__iexact=identifier)
        return user
    except User.DoesNotExist:
        return None


# From http://blog.shopfiber.com/?p=220.
# Note the comment regarding the need to add a case-insensitive index.
class CaseInsensitiveModelBackend(ModelBackend):
    """
    By default ModelBackend does case _sensitive_ username authentication, which isn't what is
    generally expected.  This backend supports case insensitive username authentication.
    """
    def authenticate(self, username=None, password=None):
        identifier = username  # Given username is actually a more generic identifier.

        user = _get_local_user(identifier)
        if user is None:
            return None
        elif user.check_password(password):
            return user
        else:
            return None


class XerocraftBackend(ModelBackend):

    def authenticate(self, username=None, password=None):

        # TODO: This would be a lot better/simpler if xerocraft.org's actions.php would offer
        # action:authenticate, SignInIdentifier:<email or username>, SignInPassword:<password>
        # that returned {auth:"yes", username:<username>, email:<email>, name:<name>} or {auth:"no"}

        identifier = username  # Given "username" is actually a more generic identifier.
        logger = logging.getLogger("xerocraft-django")
        server = "http://www.xerocraft.org/"  # Allows easy switching to test site.
        action_url = server+"actions.php"

        # Try logging in to xerocraft.org to authenticate given username and password:
        postdata = {'SignInUsername':identifier, 'SignInPassword':password, 'action':'signin'}
        response = requests.post(action_url, postdata)
        cookies = response.cookies
        if response.text.find('<a href="./index.php?logout=true">[Logout?]</a>') == -1:
            # xerocraft.org said there's no such identifier/password.
            return None

        user = _get_local_user(identifier)

        if user is not None:

            # Saving password amounts to local caching in case xerocraft.org is down.
            password_before = user.password
            user.set_password(password)
            if password_before != user.password:
                user.save()
                logger.info("Password for %s updated to match xerocraft.org.", user.username)

        else:
            # Create a new Django user based on Xerocraft.org info.
            # Since website could change, this code will assert IN PRODUCTION.

            try:
                # Scrape usernum.
                usernum_seek = 'profiles.php?id='
                usernum_start = response.text.find(usernum_seek)
                if usernum_start == -1: raise AssertionError("Couldn't find start of usernum")
                usernum_end = response.text.find('"', usernum_start)
                if usernum_end == -1: raise AssertionError("Couldn't find end of usernum")
                usernum = response.text[usernum_start+len(usernum_seek):usernum_end]
                if not usernum.isdigit(): raise AssertionError("Didn't find a numeric usernum")

                # Get the profile associated with the usernum and parse it.
                postdata = {'action':'ViewProfile', 'id':usernum, 'ax':'y'}
                response = requests.post(action_url, postdata, cookies=cookies)
                response.raise_for_status()
                profile = lxml.html.fromstring(response.text)
                if profile is None: raise AssertionError("Couldn't parse profile")

                # Scrape username
                usernames = profile.xpath("//div[@id='pp_username']/h1/text()")
                if len(usernames) == 0: raise AssertionError("Couldn't determine username")
                username = str(usernames[0])
            except (AssertionError, requests.HTTPError) as err:
                logger.error(str(err))
                return None

            # Record email if user used it as the identifier.
            email = ""  # Non-null constraint in db. Admin uses empty string.
            if '@' in identifier: email = identifier

            # Create local copy of user with info we have.
            if username is not None and password is not None:
                user = User(username=username, email=email, password=password)
                user.is_staff = False
                user.is_superuser = False
                user.save()
                logger.info("Created new user: %s", username)
            else:
                logger.error("Couldn't create local user for authenticated id: %s", identifier)

        # Xerocraft.org SERVER maintains a "logged in status" for display
        # to other users. So explicitly log out to prevent that.
        response = requests.get(server+"index.php?logout=true", cookies=cookies)
        if response.text.find('<u>Sign In Options</u>') == -1:
            logger.error("Unexpected response from xerocraft.org logout.")

        return user

