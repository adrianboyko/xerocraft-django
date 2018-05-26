
# Standard
from datetime import datetime

# Third Party
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
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
    permission_classes = [IsAuthenticatedOrReadOnly, tp.ClaimPermission]
    authentication_classes = [
        ta.NagAuthentication,
    ] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    filter_fields = {'claiming_member', 'claimed_task', 'status'}

    def get_queryset(self):
        user = self.request.user  # type: User

        if user_is_kiosk(self.request):
            return tm.Claim.objects.all().order_by('id')
        else:
            # We used to trim down the set for non-kiosk users, but won't, for now.
            return tm.Claim.objects.all().order_by('id')


# ---------------------------------------------------------------------------
# PLAYs
# ---------------------------------------------------------------------------

class PlayViewSet(viewsets.ModelViewSet):
    queryset = tm.Play.objects.all().order_by('id')
    serializer_class = ts.PlaySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, tp.PlayPermission]
    authentication_classes = [
        ta.NagAuthentication,
    ] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    filter_class = filt.PlayFilter

    def get_queryset(self):
        user = self.request.user  # type: User

        if user_is_kiosk(self.request):
            return tm.Play.objects.all().order_by('id')
        else:
            # We used to trim down the set for non-kiosk users, but won't, for now.
            return tm.Play.objects.all().order_by('id')


# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------

class TaskViewSet(viewsets.ModelViewSet):
    queryset = tm.Task.objects.all().order_by('id')
    serializer_class = ts.TaskSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, tp.TaskPermission]
    authentication_classes = [
        ta.NagAuthentication,
    ] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    filter_fields = {'scheduled_date'}

    def get_queryset(self):
        user = self.request.user  # type: User

        if user_is_kiosk(self.request):
            return tm.Task.objects.all().order_by('id')
        else:
            # We used to trim down the set for non-kiosk users, but won't, for now.
            return tm.Task.objects.all().order_by('id')


# ---------------------------------------------------------------------------
# WORKERS
# ---------------------------------------------------------------------------

class WorkerViewSet(viewsets.ModelViewSet):
    queryset = tm.Worker.objects.all().order_by('id')
    serializer_class = ts.WorkerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, tp.WorkerPermission]
    # filter_class = filt.WorkerFilter

    def get_queryset(self):

        if user_is_kiosk(self.request):
            return tm.Worker.objects.all().order_by('id')
        else:
            # We used to trim down the set for non-kiosk users, but won't, for now.
            return tm.Worker.objects.all().order_by('id')


# ---------------------------------------------------------------------------
# WORKS
# ---------------------------------------------------------------------------

class WorkViewSet(viewsets.ModelViewSet):
    queryset = tm.Work.objects.all().order_by('id')
    serializer_class = ts.WorkSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, tp.WorkPermission]
    filter_class = filt.WorkFilter

    def get_queryset(self):

        if user_is_kiosk(self.request):
            return tm.Work.objects.all().order_by('id')
        else:
            # We used to trim down the set for non-kiosk users, but won't, for now.
            return tm.Work.objects.all().order_by('id')


class WorkNoteViewSet(viewsets.ModelViewSet):
    queryset = tm.WorkNote.objects.all().order_by('id')
    serializer_class = ts.WorkNoteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):

        if user_is_kiosk(self.request):
            return tm.WorkNote.objects.all().order_by('id')
        else:
            # We used to trim down the set for non-kiosk users, but won't, for now.
            return tm.WorkNote.objects.all().order_by('id')
