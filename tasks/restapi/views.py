
# Standard
from datetime import datetime

# Third Party
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Local
import tasks.models as tm
import tasks.restapi.serializers as ts
import tasks.restapi.permissions as tp
import tasks.restapi.authenticators as ta


# ---------------------------------------------------------------------------
# CLAIMS
# ---------------------------------------------------------------------------

class ClaimViewSet(viewsets.ModelViewSet):
    queryset = tm.Claim.objects.all()
    serializer_class = ts.ClaimSerializer
    permission_classes = [IsAuthenticated, tp.ClaimPermission]
    authentication_classes = [ta.NagAuthentication]

    def get_queryset(self):
        memb = self.request.user.member

        if self.action is "list":
            # Filter to show only memb's current/future claims.
            today = datetime.today()
            return tm.Claim.objects.filter(claiming_member=memb, claimed_task__scheduled_date__gte=today)
        else:
            return tm.Claim.objects.all()


# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------

class TaskViewSet(viewsets.ModelViewSet):
    queryset = tm.Task.objects.all()
    serializer_class = ts.TaskSerializer
    permission_classes = [IsAuthenticated, tp.TaskPermission]
    authentication_classes = [ta.NagAuthentication]

    def get_queryset(self):
        memb = self.request.user.member

        if self.action is "list":
            # Filter to show only memb's current/future tasks.
            today = datetime.today()
            return tm.Task.objects.filter(owner=memb, scheduled_date__gte=today)
        else:
            return tm.Task.objects.all()


# ---------------------------------------------------------------------------
# WORKS
# ---------------------------------------------------------------------------

class WorkViewSet(viewsets.ModelViewSet):
    queryset = tm.Work.objects.all()
    serializer_class = ts.WorkSerializer
    permission_classes = [IsAuthenticated, tp.WorkPermission]

    def get_queryset(self):
        memb = self.request.user.member

        if self.action is "list":
            # Filter to show only memb's work.
            today = datetime.today()
            return tm.Work.objects.filter(claim__claiming_member=memb)
        else:
            return tm.Work.objects.all()
