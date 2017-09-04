
# Standard
import json
from logging import getLogger

# Third-party
from django.contrib.auth import authenticate
from django.http import HttpResponse, JsonResponse

# Local


logger = getLogger("xis")


def clone_acct(request) -> JsonResponse:
    """Clone an account from www.xerocraft.org to XIS."""

    if request.method == 'POST':

        data = json.loads(request.body.decode())
        username = data['username']  # type: str
        userpw = data['userpw']  # type: str

        # Cloning is accomplished by authenticator which checks xerocraft.org and caches accts in XIS.
        user = authenticate(username=username, password=userpw)
        if user is not None:
            return JsonResponse({"result": "success"})
        else:
            logger.error("Failure to clone '%s' from xerocraft.org to XIS.", username)
            return JsonResponse(status=401, data={"result": "failure"})
