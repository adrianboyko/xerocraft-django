
# Standard

# Third Party
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import permissions
from rest_framework.request import Request

# Local
import members.models as mm
import tasks.models as tm
from xis.utils import user_is_kiosk


def getpk(uri: str) -> int:
    assert(uri.endswith('/'))
    return int(uri.split('/')[-2])


# ---------------------------------------------------------------------------
# CLAIMS
# ---------------------------------------------------------------------------

class ClaimPermission(permissions.BasePermission):

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

            claimed_task_pk = getpk(request.data["claimed_task"])
            claiming_member_pk = getpk(request.data["claiming_member"])
            calling_member_pk = request.user.member.pk

            if calling_member_pk != claiming_member_pk:
                # Only allowing callers to create their own claims.
                return False

            claiming_member = mm.Member.objects.get(pk=claiming_member_pk)
            claimed_task = tm.Task.objects.get(pk=claimed_task_pk)  # type: tm.Task

            # Not allowed to claim a task that's already fully claimed.
            if request.data["status"] == tm.Claim.STAT_CURRENT:
                if claimed_task.is_fully_claimed:
                    return False

            if claiming_member not in claimed_task.eligible_claimants.all():
                # Don't allow non-eligible claimant.
                return False

            return True

        else:
            return False

    def has_object_permission(self, request: Request, view, obj):
        memb = request.user.member  # type: mm.Member

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ["PUT", "PATCH"]:
            if user_is_kiosk(request):
                return True

        if memb == obj.claiming_member:
            # The claiming_member is the owner of a Claim.
            return True


# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------

class TaskPermission(permissions.BasePermission):

    def has_object_permission(self, request: Request, view, obj):
        user = request.user  # type: User
        memb = user.member  # type: mm.Member

        if request.method in permissions.SAFE_METHODS:
            return True
        # Might want to do this or aggregate DangoModelPermissions instead.
        # elif user.is_staff:
        #     if request.method is 'POST':
        #         return user.has_perm("tasks.add_task")
        #     elif request.method is 'PUT':
        #         return user.has_perm("tasks.change_task")
        #     elif request.method is 'DELETE':
        #         return user.has_perm("tasks.delete_task")
        #     else:
        #         return False
        else:
            return memb == obj.owner


# ---------------------------------------------------------------------------
# WORKS
# ---------------------------------------------------------------------------

# REVIEW: Is there a cleaner alternative?
def get_resnum_from_url(resurl: str) -> int:
    parts = resurl.split("/")
    resnum = parts[-2]
    return int(resnum)


class WorkPermission(permissions.BasePermission):

    def has_object_permission(self, request: Request, view, obj: tm.Work) -> bool:
        memb = request.user.member  # type: mm.Member

        # Only allow the witness to be set if
        #  1) the request has the witness PW in a header, and
        #  2) the witness name & pw authenticate.
        if request.method in ("PUT", "PATCH"):
            witness_url = request.data.get("witness")
            if witness_url is not None:
                witness_pw = request.META.get("HTTP_X_WITNESS_PW")
                if witness_pw is None:
                    return False
                witness_id = get_resnum_from_url(witness_url)
                try:
                    witness = mm.Member.objects.get(id=witness_id)
                except mm.Member.DoesNotExist:
                    return False
                if not authenticate(request, username=witness.username, password=witness_pw):
                    return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if type(obj) is tm.Work:
            return memb == obj.claim.claiming_member or user_is_kiosk(request)
