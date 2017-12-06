
# Standard
from datetime import datetime

# Third Party
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings

# Local
from members.models import Member
import tasks.models as tm
import tasks.restapi.serializers as ts
import tasks.restapi.permissions as tp
import tasks.restapi.authenticators as ta
import tasks.restapi.filter as filt
from xis.utils import user_is_kiosk

# ---------------------------------------------------------------------------
# CLAIMS
# ---------------------------------------------------------------------------

class ClaimViewSet(viewsets.ModelViewSet):
    queryset = tm.Claim.objects.all().order_by('id')
    serializer_class = ts.ClaimSerializer
    permission_classes = [IsAuthenticated, tp.ClaimPermission]
    authentication_classes = [
        ta.NagAuthentication,
    ] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    filter_fields = {'claiming_member', 'claimed_task', 'status'}

    def get_queryset(self):
        user = self.request.user  # type: User
        memb = user.member  # type: Member

        if user_is_kiosk(self.request):
            return tm.Claim.objects.all().order_by('id')
        else:
            if self.action is "list":
                # Filter to show only memb's current/future claims.
                today = datetime.today()
                return tm.Claim.objects.filter(claiming_member=memb, claimed_task__scheduled_date__gte=today).order_by('id')
            else:
                return tm.Claim.objects.all().order_by('id')


# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------

class TaskViewSet(viewsets.ModelViewSet):
    queryset = tm.Task.objects.all().order_by('id')
    serializer_class = ts.TaskSerializer
    permission_classes = [IsAuthenticated, tp.TaskPermission]
    authentication_classes = [
        ta.NagAuthentication,
    ] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    filter_fields = {'scheduled_date'}

    def get_queryset(self):
        user = self.request.user  # type: User
        memb = user.member  # type: Member

        if user_is_kiosk(self.request):
            return tm.Task.objects.all().order_by('id')
        else:
            # Limit what other authenticated users can see.
            if self.action is "list":
                # Filter to show only memb's current/future tasks.
                today = datetime.today()
                return tm.Task.objects.filter(owner=memb, scheduled_date__gte=today)
            else:
                return tm.Task.objects.all().order_by('id')


# ---------------------------------------------------------------------------
# WORKS
# ---------------------------------------------------------------------------

class WorkViewSet(viewsets.ModelViewSet):
    queryset = tm.Work.objects.all().order_by('id')
    serializer_class = ts.WorkSerializer
    permission_classes = [IsAuthenticated, tp.WorkPermission]
    filter_class = filt.WorkFilter

    def get_queryset(self):
        memb = self.request.user.member

        if user_is_kiosk(self.request):
            return tm.Work.objects.all().order_by('id')

        if self.action is "list":
            # Filter to show only memb's work.
            today = datetime.today()
            return tm.Work.objects.filter(claim__claiming_member=memb)
        else:
            return tm.Work.objects.all().order_by('id')
