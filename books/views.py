from django.shortcuts import render
from rest_framework import viewsets
from .serializers import *


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = SALE REST API

class SaleViewSet(viewsets.ModelViewSet):  # Django REST Framework
    """
    API endpoint that allows paid memberships to be viewed or edited.
    """
    queryset = Sale.objects.all().order_by('-sale_date')
    serializer_class = SaleSerializer
    filter_fields = {'payment_method', 'ctrlid'}


class SaleNoteViewSet(viewsets.ModelViewSet):  # Django REST Framework
    """
    API endpoint that allows memberships to be viewed or edited.
    """
    queryset = SaleNote.objects.all().order_by('-sale')
    serializer_class = SaleNoteSerializer


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = DONATION REST API

class DonationViewSet(viewsets.ModelViewSet):  # Django REST Framework
    """
    API endpoint that allows paid memberships to be viewed or edited.
    """
    queryset = Donation.objects.all().order_by('-donation_date')
    serializer_class = DonationSerializer
    #filter_fields = {'ctrlid'}


class DonationNoteViewSet(viewsets.ModelViewSet):  # Django REST Framework
    """
    API endpoint that allows memberships to be viewed or edited.
    """
    queryset = DonationNote.objects.all().order_by('-donation')
    serializer_class = DonationNoteSerializer


class PhysicalDonationViewSet(viewsets.ModelViewSet):  # Django REST Framework
    """
    API endpoint that allows memberships to be viewed or edited.
    """
    queryset = PhysicalDonation.objects.all().order_by('-donation')
    serializer_class = PhysicalDonationSerializer


class MonetaryDonationViewSet(viewsets.ModelViewSet):  # Django REST Framework
    """
    API endpoint that allows memberships to be viewed or edited.
    """
    queryset = MonetaryDonation.objects.all().order_by('-donation')
    serializer_class = MonetaryDonationSerializer

