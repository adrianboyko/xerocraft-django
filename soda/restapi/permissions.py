
# Standard
import logging

# Third Party
from rest_framework import permissions
from rest_framework.request import Request
from django.shortcuts import get_object_or_404

# Local
import soda.models as sm
from xis.utils import user_is_kiosk


def getpk(uri: str) -> int:
    assert(uri.endswith('/'))
    return int(uri.split('/')[-2])


_logger = logging.getLogger("soda")


# ---------------------------------------------------------------------------
# VEND LOG
# ---------------------------------------------------------------------------

class VendLogPermission(permissions.BasePermission):

    def has_permission(self, request: Request, view) -> bool:

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ["PATCH", "PUT"]:
            return False

        if request.method == "POST" and user_is_kiosk(request):

            # DRF's web interface sends POST with no body to determine if
            # a read/write or read-only options should be presented.
            datalen = request.META.get('CONTENT_LENGTH', '0')  # type: str
            if datalen == '0' or datalen == '':
                return True

            product = get_object_or_404(sm.Product, pk=request.POST["product"])
            return product.is_in_machine

        return False

    def has_object_permission(self, request: Request, view, log: sm.VendLog) -> bool:

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ("PUT", "PATCH"):
            return False

        return False

