
# Standard
from hashlib import md5
import datetime as dt

# Third Pary
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

# Local
import tasks.models as tm


class NagAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):

        nagtoken = request.META.get('HTTP_X_NAGTOKEN')  # type: str

        # Was a token passed?
        if not nagtoken:
            return None  # failure, no token.

        # Is it a real token?
        md5str = md5(nagtoken.encode()).hexdigest()
        try:
            nag = tm.Nag.objects.get(auth_token_md5=md5str)  # type: tm.Nag
        except tm.Nag.DoesNotExist:
            return None  # failure, invalid token

        # Has the token expired?
        age = nag.when.date() - dt.date.today()  # type: dt.timedelta
        if age.days > 30:
            return None # failure, expired token

        # Everything is good
        return nag.who.auth_user, None
