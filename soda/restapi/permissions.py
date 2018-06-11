
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

    def has_object_permission(self, request: Request, view, obj: sm.VendLog) -> bool:

        memb = request.user.member  # type: mm.Member

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ("PUT", "PATCH"):
            return user_is_kiosk(request)

        # REVIEW: Why is this needed?
        if type(obj) is sm.VendLog:
            return user_is_kiosk(request)

        return False

