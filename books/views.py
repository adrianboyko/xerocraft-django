from django.shortcuts import render
from rest_framework import viewsets
from .serializers import *


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = SALE REST API

class SaleViewSet(viewsets.ModelViewSet):  # Django REST Framework
    queryset = Sale.objects.all().order_by('-sale_date')
    serializer_class = SaleSerializer
    filter_fields = {'payment_method', 'ctrlid'}


class SaleNoteViewSet(viewsets.ModelViewSet):  # Django REST Framework
    queryset = SaleNote.objects.all().order_by('-sale')
    serializer_class = SaleNoteSerializer


class OtherItemViewSet(viewsets.ModelViewSet):  # Django REST Framework
    queryset = OtherItem.objects.all()
    serializer_class = OtherItemSerializer
    filter_fields = {'ctrlid'}


class OtherItemTypeViewSet(viewsets.ModelViewSet):  # Django REST Framework
    queryset = OtherItemType.objects.all()
    serializer_class = OtherItemTypeSerializer
    filter_fields = {'name'}


class MonetaryDonationViewSet(viewsets.ModelViewSet):  # Django REST Framework
    """
    API endpoint that allows monetary donations to be viewed or edited.
    """
    queryset = MonetaryDonation.objects.all().order_by('-donation')
    serializer_class = MonetaryDonationSerializer
    filter_fields = {'ctrlid'}


