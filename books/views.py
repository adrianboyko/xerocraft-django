
# Standard
from datetime import date, datetime

# Third Party
from django.shortcuts import render
from rest_framework import viewsets
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
import numpy as np
from dateutil.parser import parse

# Local
from .models import (
    ExpenseLineItem,
    Sale, SaleNote,
    MonetaryDonation,
    OtherItem, OtherItemType
)
from .serializers import (
    SaleSerializer, SaleNoteSerializer,
    MonetaryDonationSerializer,
    OtherItemSerializer, OtherItemTypeSerializer
)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def _acc(pts):
    """ Accumulates """
    acc_vs_time = []
    acc_to_date = 0.0
    pts.sort(key=lambda pt: pt[0])
    for x in pts:
        acc_to_date += x[1]
        acc_vs_time.append([x[0], acc_to_date])
    return acc_vs_time


def _fits(pts):

    cols = list(zip(*pts))
    iso_dates = cols[0]
    xs = [parse(x).timestamp() for x in iso_dates]
    ys = cols[1]

    # Polynomial fit
    [x2, x1, x0] = np.polyfit(xs, ys, 2)
    poly_y0 = x2*xs[0]*xs[0] + x1*xs[0] + x0

    # Linear comparison
    m = 2 * x2 * xs[0] + x1
    lin_ys = [m*(x - xs[0]) + poly_y0 for x in xs]

    return zip(iso_dates, ys, lin_ys)


@login_required
def cumulative_vs_date_chart(request):

    # TODO: Turn this into a @directors_only decorator that uses @login_required
    # REVIEW: This creates a dependency on "members". Review members/books relationship.
    if not request.user.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")

    start = date(2016, 1, 1)

    data = []

    exps = []
    for exp in ExpenseLineItem.objects.all():
        if exp.expense_date < start:
            continue
        pt = [exp.expense_date.isoformat(), -1.0 * float(exp.amount)]
        exps.append(pt)
        data.append(pt)

    incs = []
    for inc in Sale.objects.all():  # AKA IncomeTransactions
        if inc.sale_date <= start:
            continue

        # Bit Buckets "what if?"
        if request.path.endswith("/2/"):
            if inc.payer_name.lower().startswith("bit"):
                continue

        pt = [inc.sale_date.isoformat(), float(inc.total_paid_by_customer - inc.processing_fee)]
        incs.append(pt)
        data.append(pt)

    acc_inc_vs_time = _acc(incs)
    acc_exp_vs_time = _acc(exps)
    acc_net_vs_time = _acc(data)

    acc_inc_vs_time = _fits(acc_inc_vs_time)
    acc_exp_vs_time = _fits(acc_exp_vs_time)

    params = {
        'net': acc_net_vs_time,
        'inc': acc_inc_vs_time,
        'exp': acc_exp_vs_time,
    }
    return render(request, 'books/cumulative-vs-date-chart.html', params)


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


