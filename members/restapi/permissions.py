# Standard

# Third Party
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import permissions
from rest_framework.request import Request

# Local
import members.models as mm
from xis.utils import user_is_kiosk


# ---------------------------------------------------------------------------
# VISIT EVENT
# ---------------------------------------------------------------------------

class VisitEventPermission(permissions.BasePermission):

    def has_permission(self, request: Request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            user_is_kiosk(request)

    def has_object_permission(self, request: Request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            user_is_kiosk(request)
