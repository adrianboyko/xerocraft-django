import requests
import logging
import time
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


# TODO: Add case insensitive index to User.username per comments below.
# TODO: Email address authentication

# From http://blog.shopfiber.com/?p=220.
# Note the comment regarding the need to add a case-insensitive index.
class CaseInsensitiveModelBackend(ModelBackend):
    """
    By default ModelBackend does case _sensitive_ username authentication, which isn't what is
    generally expected.  This backend supports case insensitive username authentication.
    """
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
            else:
                return None
        except User.DoesNotExist:
            return None


class XerocraftBackend(ModelBackend):

    def authenticate(self, username=None, password=None):

        logger = logging.getLogger("xerocraft-django")

        # Try logging in to xerocraft.org to authenticate given username and password:
        postdata = {'SignInUsername':username, 'SignInPassword':password, 'action':'signin' }
        response = requests.post("http://xerocraft.org/actions.php", postdata)
        if response.text.find('<a href="./index.php?logout=true">[Logout?]</a>') != -1:
            try:
                user = User.objects.get(username__iexact=username)  # Will necessitate case-insensitive index.
                # Saving password amounts to local caching in case xerocraft.org is down.
                password_before = user.password
                user.set_password(password)
                if password_before != user.password:
                    logger.info("Password for %s updated to match xerocraft.org.", username)
            except User.DoesNotExist:
                user = User(username=username, password=password)
                user.is_staff = False
                user.is_superuser = False
                logger.info("Created new user: %s", username)
            user.save()

            # Xerocraft.org SERVER maintains a "logged in status" for display
            # to other users. So explicitly log out to prevent that.
            # TODO: Does this work without providing a cookie?
            response = requests.get("http://xerocraft.org/index.php?logout=true")
            if response.text.find('<u>Sign In Options</u>') == -1:
                logger.error("Unexpected response from xerocraft.org logout.")

            return user

        return None

