
# Standard

# Third-Party
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

# Local
import kmkr.restapi.serializers as ser
import kmkr.models as mod


class PlayLogEntryViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows PlayLogEntries to be viewed or edited.
    """
    queryset = mod.PlayLogEntry.objects.all().order_by('-start')
    serializer_class = ser.PlayLogEntrySerializer
    filter_fields = {'start', 'show', 'show_date'}
    ordering_fields = {'start'}
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class ShowViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows Shows to be viewed or edited.
    """
    queryset = mod.Show.objects.all().order_by('pk')
    serializer_class = ser.ShowSerializer
    filter_fields = {}
    ordering_fields = {}
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

