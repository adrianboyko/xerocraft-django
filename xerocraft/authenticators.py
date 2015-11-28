import requests
import logging
import time
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class XerocraftBackend(ModelBackend):

    def authenticate(self, username=None, password=None):

        logger = logging.getLogger("xerocraft-django")

        # Make sure we're logged out of xerocraft.org:
        response = requests.get("http://xerocraft.org/index.php?logout=true")
        if response.text.find('<u>Sign In Options</u>') == -1:
            logger.error("Unexpected response from xerocraft.org logout.")
            return None

        # Now try logging in to xerocraft.org to authenticate given username and password:
        postdata = {'SignInUsername':username, 'SignInPassword':password, 'action':'signin' }
        response = requests.post("http://xerocraft.org/actions.php", postdata)
        if response.text.find('<a href="./index.php?logout=true">[Logout?]</a>') != -1:
            try:
                user = User.objects.get(username=username)
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
            return user
        return None

