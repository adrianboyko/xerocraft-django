
# Standard

# Third-Party
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.authentication import BasicAuthentication

# Local
from .. import models as mod
from . import filters as filt
from . import serializers as ser


class BroadcastViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows Broadcasts to be viewed or edited.
    """
    queryset = mod.Broadcast.objects.all().order_by('pk')
    serializer_class = ser.BroadcastSerializer
    filter_fields = {'episode', 'type'}
    ordering_fields = {}
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    authentication_classes = [BasicAuthentication]


class PlayLogEntryViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows PlayLogEntries to be viewed or edited.
    """
    queryset = mod.PlayLogEntry.objects.all().order_by('-start')
    serializer_class = ser.PlayLogEntrySerializer
    filter_fields = {'start'}
    ordering_fields = {'start'}
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    authentication_classes = [BasicAuthentication]


class ShowViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows Shows to be viewed or edited.
    """
    queryset = mod.Show.objects.all().order_by('pk')
    serializer_class = ser.ShowSerializer
    filter_fields = {}
    ordering_fields = {}
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class EpisodeViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows Episodes to be viewed or edited.
    """
    queryset = mod.Episode.objects.all().order_by('pk')
    serializer_class = ser.EpisodeSerializer
    filter_class = filt.EpisodeFilter
    ordering_fields = {}
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    authentication_classes = [BasicAuthentication]


class EpisodeTrackViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows Episode Tracks to be viewed or edited.
    """
    queryset = mod.EpisodeTrack.objects.all().order_by('pk')
    serializer_class = ser.EpisodeTrackSerializer
    filter_fields = {}
    ordering_fields = {}
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    authentication_classes = [BasicAuthentication]


class TrackViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows Tracks to be viewed or edited.
    """
    queryset = mod.Track.objects.all().order_by('pk')
    serializer_class = ser.TrackSerializer
    filter_fields = {}
    ordering_fields = {}
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
