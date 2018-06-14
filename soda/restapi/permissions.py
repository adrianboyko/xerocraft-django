
# Standard

# Third Party
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import permissions
from rest_framework.request import Request

# Local
import members.models as mm
import soda.models as sm
from xis.utils import user_is_kiosk


def getpk(uri: str) -> int:
    assert(uri.endswith('/'))
    return int(uri.split('/')[-2])


# ---------------------------------------------------------------------------
# PLAYS
# ---------------------------------------------------------------------------

class VendLogPermission(permissions.BasePermission):

    def has_permission(self, request: Request, view) -> bool:

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ["PATCH", "PUT"]:
            # I believe this is safe because Django subsequently goes to has_object_permissions
            return True

        if request.method == "POST":
            if user_is_kiosk(request):
                return True
            # Web interface to REST API sends POST with no body to determine if
            # a read/write or read-only interface should be presented. In general,
            # anybody can post a claim, so we'll return True for this case.
            datalen = request.META.get('CONTENT_LENGTH', '0')  # type: str
            if datalen == '0' or datalen == '':
                return True

        return False

    def has_object_permission(self, request: Request, view, obj: sm.VendLog) -> bool:

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ("PUT", "PATCH"):
            return user_is_kiosk(request)

        # REVIEW: Why is this needed?
        if type(obj) is sm.VendLog:
            return user_is_kiosk(request)

        return False

