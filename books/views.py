
# Standard
from datetime import date

# Third Party
from django.shortcuts import render
from rest_framework import viewsets
from django.http.response import HttpResponse

# Local
from .serializers import *


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def net_income_vs_date_chart(request):
    u = request.user
    if u.is_anonymous() or not u.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")

    start = date(2016, 1, 1)
    data = []
    for exp in ExpenseLineItem.objects.all():
        if exp.expense_date < start:
            continue
        data.append([exp.expense_date.isoformat(), -1.0*float(exp.amount)])
    incs = []
    for inc in Sale.objects.all():  # AKA IncomeTransactions
        if inc.sale_date <= start:
            continue
        data.append([inc.sale_date.isoformat(), float(inc.total_paid_by_customer - inc.processing_fee)])
    # http://stackoverflow.com/questions/464342/combining-two-sorted-lists-in-python
    data.sort(key=lambda pt: pt[0])
    acc_income_vs_time = []
    acc_income_to_date = 0.0
    for x in data:
        acc_income_to_date += x[1]
        acc_income_vs_time.append([x[0], acc_income_to_date])
    return render(request, 'books/net-income-vs-date-chart.html', {'data': acc_income_vs_time})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def net_income_vs_date_chart_2(request):  # This is a temporary view
    u = request.user
    if u.is_anonymous() or not u.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")

    start = date(2016, 1, 1)
    data = []
    for exp in ExpenseLineItem.objects.all():
        if exp.expense_date < start:
            continue
        data.append([exp.expense_date.isoformat(), -1.0*float(exp.amount)])
    incs = []
    for inc in Sale.objects.all():  # AKA IncomeTransactions
        if inc.sale_date <= start:
            continue
        if inc.payer_name.lower().startswith("bit"):
            continue
        data.append([inc.sale_date.isoformat(), float(inc.total_paid_by_customer - inc.processing_fee)])
    # http://stackoverflow.com/questions/464342/combining-two-sorted-lists-in-python
    data.sort(key=lambda pt: pt[0])
    acc_income_vs_time = []
    acc_income_to_date = 0.0
    for x in data:
        acc_income_to_date += x[1]
        acc_income_vs_time.append([x[0], acc_income_to_date])
    return render(request, 'books/net-income-vs-date-chart.html', {'data': acc_income_vs_time})


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
    queryset = MonetaryDonation.objects.all().order_by('-sale')
    serializer_class = MonetaryDonationSerializer
    filter_fields = {'ctrlid'}


