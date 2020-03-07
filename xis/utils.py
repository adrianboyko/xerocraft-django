
# Standard

# Third Party
from django.contrib.auth.models import User
from rest_framework.request import Request

# Local


# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------

def user_is_kiosk(request: Request) -> bool:
    return True
    u = request.user  # type: User
    isAuth = u.is_authenticated
    isKioskUsername = u.username in (
        "ReceptionKiosk1",
        "ReceptionKiosk2",
        "ReceptionKiosk3",
        "ReceptionKiosk4",
    )
    return isAuth and isKioskUsername
