
# Core
from datetime import datetime

# Third Party
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import permissions

# Local
import tasks.models as tm
import tasks.serializers as ts
import members.models as mm


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        memb = request.user.member  # type: mm.Member

        if request.method in permissions.SAFE_METHODS:
            return True

        if type(obj) is tm.Claim:
            if memb == obj.claiming_member:
                # The claiming_member is the owner of a Claim.
                return True
            else:
                # Otherwise, permission is the same as the permission on the claimed_task.
                # Note that this means that owners of task T will be owners of Claims on T.
                return self.has_object_permission(request, view, obj.claimed_task)

        if type(obj) is tm.Task:
            if memb == obj.owner:
                return True
            else:
                return False


class ClaimViewSet(viewsets.ModelViewSet):
    queryset = tm.Claim.objects.all()
    serializer_class = ts.ClaimSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        memb = self.request.user.member

        if self.action is "list":
            # Filter to show only memb's current/future claims.
            today = datetime.today()
            return tm.Claim.objects.filter(claiming_member=memb, claimed_task__scheduled_date__gte=today)
        else:
            return tm.Claim.objects.all()


class TaskViewSet(viewsets.ModelViewSet):
    queryset = tm.Task.objects.all()
    serializer_class = ts.TaskSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_fields = []

    def get_queryset(self):
        memb = self.request.user.member

        if self.action is "list":
            # Filter to show only memb's current/future tasks.
            today = datetime.today()
            return tm.Task.objects.filter(owner=memb, scheduled_date__gte=today)
        else:
            return tm.Task.objects.all()
