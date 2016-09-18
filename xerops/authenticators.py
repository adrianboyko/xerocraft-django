
# Standard

# Third Party
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

# Local
from members.models import Member


# From http://blog.shopfiber.com/?p=220.
# Note the comment regarding the need to add a case-insensitive index.
class CaseInsensitiveModelBackend(ModelBackend):
    """
    By default ModelBackend does case _sensitive_ username authentication, which isn't what is
    generally expected. This backend supports case insensitive username authentication.
    """
    def authenticate(self, username=None, password=None):
        identifier = username  # Given username is actually a more generic identifier.

        # Member.get_local_user() is case-insensitive
        user = Member.get_local_user(identifier)  # type: User
        if user is None:
            return None
        elif user.check_password(password):
            return user
        else:
            return None

