
# Core

# Third Party
from rest_framework import viewsets

# Local
import tasks.models as tm
import tasks.serializers as ts


class TaskViewSet(viewsets.ModelViewSet):
    queryset = tm.Task.objects.all()
    serializer_class = ts.TaskSerializer

