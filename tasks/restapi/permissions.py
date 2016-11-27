
# Standard
from datetime import datetime

# Third Party
from rest_framework import permissions
from rest_framework.request import Request

# Local
import members.models as mm
import tasks.models as tm
import tasks.restapi.serializers as ts


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

        if request.method == "PATCH":
            # I believe this is safe because Django subsequently goes to has_object_permissions
            return True

        if request.method == "POST":

            # Web interface to REST API sends POST with no body to determine if
            # a read/write or read-only interface should be presented. In general,
            # anybody can post a claim, so we'll return True for this case.
            datalen = request.META.get('CONTENT_LENGTH')  # type: str
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

            if claiming_member not in claimed_task.eligible_claimants.all():
                # Don't allow non-eligible claimant.
                return False

            return True

        else:
            return False

    def has_object_permission(self, request, view, obj):
        memb = request.user.member  # type: mm.Member

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method is "PUT":
            pass

        if memb == obj.claiming_member:
            # The claiming_member is the owner of a Claim.
            return True
        else:
            # Otherwise, permission is the same as the permission on the claimed_task.
            # Note that this means that owners of task T will be owners of Claims on T.
            return self.has_object_permission(request, view, obj.claimed_task)


# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------

class TaskPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        memb = request.user.member  # type: mm.Member

        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return memb == obj.owner


# ---------------------------------------------------------------------------
# WORKS
# ---------------------------------------------------------------------------

class WorkPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        memb = request.user.member  # type: mm.Member

        if request.method in permissions.SAFE_METHODS:
            return True

        if type(obj) is tm.Work:
            return memb == obj.claim.claiming_member
