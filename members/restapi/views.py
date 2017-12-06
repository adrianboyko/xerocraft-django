
# Standard

# Third-Party
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

# Local
import members.restapi.serializers as ser
import members.restapi.filters as filt
from members.models import (
    Member,
    Membership,
    DiscoveryMethod,
    MembershipGiftCardReference,
    WifiMacDetected,
)


class MemberViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows members to be viewed or edited.
    """
    queryset = Member.objects.all()
    serializer_class = ser.get_MemberSerializer(True)  # Default to privacy.
    permission_classes = [IsAuthenticated]
    filter_backends = viewsets.ModelViewSet.filter_backends + [filt.HasRfidNumFilterBackend]
    filter_class = filt.MemberFilter

    def retrieve(self, request, pk=None):
        memb = get_object_or_404(self.queryset, pk=pk)

        with_privacy = True
        is_director = request.user.member.is_tagged_with("Director")
        is_staff = request.user.member.is_tagged_with("Staff")
        is_self = request.user.member.pk == memb.pk
        if is_director or is_staff or is_self:
            with_privacy = False

        slizer = ser.get_MemberSerializer(with_privacy)(memb, context={'request': request})
        return Response(slizer.data)


class MembershipViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows memberships to be viewed or edited.
    """
    queryset = Membership.objects.all().order_by('-start_date')
    serializer_class = ser.MembershipSerializer
    filter_fields = {'ctrlid', 'member'}
    ordering_fields = {'start_date'}


class DiscoveryMethodViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows discovery methods to be viewed or edited.
    """
    queryset = DiscoveryMethod.objects.all().order_by('order')
    serializer_class = ser.DiscoveryMethodSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class MembershipGiftCardReferenceViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows memberships to be viewed or edited.
    """
    queryset = MembershipGiftCardReference.objects.all()
    serializer_class = ser.MembershipGiftCardReferenceSerializer
    filter_fields = {'ctrlid'}


class WifiMacDetectedViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint that allows WiFi MAC detections to be logged.
    """
    queryset = WifiMacDetected.objects.all()
    serializer_class = ser.WifiMacDetectedSerializer

