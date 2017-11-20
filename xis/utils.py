
# Standard

# Third Party
from django.contrib.auth.models import User
from rest_framework.request import Request

# Local


# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------

def user_is_kiosk(request: Request) -> bool:
    u = request.user  # type: User
    return u.is_authenticated() and u.username in ("ReceptionKiosk1", "ReceptionKiosk2")
