
# Standard
from datetime import date, datetime
from logging import getLogger
from typing import List
import json
from decimal import Decimal

# Third Party
from django.shortcuts import render
from rest_framework import viewsets
from django.http.response import HttpResponse
from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import settings
from django.shortcuts import get_object_or_404
import requests

# import numpy as np
# from dateutil.parser import parse

# Local
from .models import (
    Account, ACCT_ASSET_CASH,
    Sale, SaleNote, Note,
    MonetaryDonation,
    OtherItem, OtherItemType,
    Journaler, JournalEntry, JournalEntryLineItem
)
from .serializers import (
    SaleSerializer, SaleNoteSerializer,
    MonetaryDonationSerializer,
    OtherItemSerializer, OtherItemTypeSerializer
)
import members.notifications as notifications  # Temporary
from members.models import Member  # Temporary

_logger = getLogger("books")

SQUAREUP_APIV1_TOKEN = settings.BZWOPS_BOOKS_CONFIG['SQUAREUP_APIV1_TOKEN']


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


# def _fits(pts):
#
#     cols = list(zip(*pts))
#     iso_dates = cols[0]
#     xs = [parse(x).timestamp() for x in iso_dates]
#     ys = cols[1]
#
#     # Index of the point on the poly fit at which the tangential linear comparison will be calculated
#     tan_ndx = 0  # int(len(xs)/2)
#
#     # Polynomial fit
#     [x2, x1, x0] = np.polyfit(xs, ys, 2)
#     tan_y = x2*xs[tan_ndx]*xs[tan_ndx] + x1*xs[tan_ndx] + x0
#
#     # claculate the tangential linear comparison y values
#     m = 2 * x2 * xs[tan_ndx] + x1
#     lin_ys = [m*(x - xs[tan_ndx]) + tan_y for x in xs]
#
#     return zip(iso_dates, ys, lin_ys)
#
#

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


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def journalentry_view(request, journaler: Journaler):

    params = {
        'is_popup': False,
        'title': "Journal Entries for {}".format(journaler),
        'journaler': journaler,
        # TODO: Instead of one je, get the list of journal entries that have source_url == journaler.
        #'journal_entries': [journaler.journal_entry],
        'journal_entries': JournalEntry.objects.filter(source_url=journaler.get_absolute_url()).all()
    }
    return render(request, 'books/journal-entries.html', params)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@login_required
def revenues_and_expenses_from_journal(request):

    # TODO: Turn this into a @directors_only decorator that uses @login_required
    # REVIEW: This creates a dependency on "members". Review members/books relationship.
    if not request.user.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")

    start = date(2015, 1, 1)
    end = date.today()

    def get_data(category, factor):
        data = []
        for jeli in JournalEntryLineItem.objects.filter(
          account__category=category,
          journal_entry__when__gte=start,
          journal_entry__when__lte=end).prefetch_related('journal_entry'):  # type: JournalEntryLineItem
            pt = [jeli.journal_entry.when.isoformat(), factor * float(jeli.amount)]
            data.append(pt)
        return data

    rev = get_data(Account.CAT_REVENUE, 1.0)
    exp = get_data(Account.CAT_EXPENSE, -1.0)

    net = rev+exp
    acc_rev_vs_time = _acc(rev)
    acc_exp_vs_time = _acc(exp)
    acc_net_vs_time = _acc(net)

    params = {
        'net': acc_net_vs_time,
        'rev': acc_rev_vs_time,
        'exp': acc_exp_vs_time,
    }
    return render(request, 'books/cumulative-rev-exp-chart.html', params)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@csrf_exempt
def squareup_webhook(request):

    _logger.info(request.body)

    # For sending notice via Pushover:
    recipient = Member.objects.get(auth_user__username='adrianb')

    json_body = json.loads(request.body.decode())
    location_id = json_body['location_id']
    payment_id = json_body['entity_id']
    event_type = json_body['event_type']

    get_headers = {
        'Authorization': "Bearer " + SQUAREUP_APIV1_TOKEN,
        'Accept': "application/json",
    }

    try:
        payment_url = "https://connect.squareup.com/v1/{}/payments/{}".format(location_id, payment_id)
        response = requests.get(payment_url, headers=get_headers)
        response.raise_for_status()
        itemizations = json.loads(response.text)['itemizations']
        for item in itemizations:
            sku = item['item_detail']['sku']
            qty = int(float(item['quantity']))
            msg = "{}, qty {}".format(sku, qty)
            notifications.notify(recipient, "SquareUp Purchase", msg)

        return HttpResponse("Ok")
    except requests.exceptions.ConnectionError:
        _logger.error("Couldn't purchase info from SquareUp.")
        return HttpResponse("Error")


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def chart_of_accounts(request: HttpRequest):

    def flatten_and_label(accts: List[Account]) -> List[Account]:
        result = []
        for acct in accts:
            result.append(acct)
            subaccts = list(acct.account_set.all())
            for acct in flatten_and_label(subaccts):
                result.append(acct)
        return result

    asset_root_accts = list(Account.objects.filter(parent=None, category=Account.CAT_ASSET))  # type: List[Account]
    expense_root_accts = list(Account.objects.filter(parent=None, category=Account.CAT_EXPENSE))  # type: List[Account]
    liability_root_accts = list(Account.objects.filter(parent=None, category=Account.CAT_LIABILITY))  # type: List[Account]
    equity_root_accts = list(Account.objects.filter(parent=None, category=Account.CAT_EQUITY))  # type: List[Account]
    revenue_root_accts = list(Account.objects.filter(parent=None, category=Account.CAT_REVENUE))  # type: List[Account]

    params = {
        'asset_accts': flatten_and_label(asset_root_accts),
        'expense_accts': flatten_and_label(expense_root_accts),
        'liability_accts': flatten_and_label(liability_root_accts),
        'equity_accts': flatten_and_label(equity_root_accts),
        'revenue_accts': flatten_and_label(revenue_root_accts),
    }

    return render(request, 'books/chart-of-accounts.html', params)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@login_required
def cash_balances_vs_time(request):

    # TODO: Turn this into a @directors_only decorator that uses @login_required
    # REVIEW: This creates a dependency on "members". Review members/books relationship.
    if not request.user.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")

    start = date(2015, 1, 1)
    end = date.today()

    def get_xis_pts_for(acct: Account):
        data = []
        for jeli in JournalEntryLineItem.objects.filter(
          account=acct,
          journal_entry__when__gte=start,
          journal_entry__when__lte=end):  # type: JournalEntryLineItem
            factor = 1.0 if jeli.action == jeli.ACTION_BALANCE_INCREASE else -1.0
            pt = [jeli.journal_entry.when.isoformat(), factor * float(jeli.amount)]
            data.append(pt)
        return data

    cash_root = Account.get(ACCT_ASSET_CASH)  # type: Account
    xis_accts = cash_root.subaccounts  # type: List[Account]
    xis_accts.append(cash_root)  # type: List[Account]
    xis_pts = []
    for acct in xis_accts:
        xis_pts.extend(get_xis_pts_for(acct))
    xis_pts = _acc(xis_pts)

    params = {'xis_pts': xis_pts}

    return render(request, 'books/cash-balances-vs-time.html', params)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@login_required
def items_needing_attn(request):

    notes_needing_attn = []
    for note_class in Note.__subclasses__():
        notes = note_class.objects.filter(needs_attn=True).all()
        notes_needing_attn.extend(list(notes))

    unbalanced_journal_entries = JournalEntry.objects.filter(unbalanced=True).all()
    params = {
        'notes_needing_attn': notes_needing_attn,
        'unbalanced_journal_entries': unbalanced_journal_entries,
    }
    return render(request, 'books/items-needing-attn.html', params)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@login_required
def account_history(request, account_pk: int, begin_date: str, end_date: str):

    acct = get_object_or_404(Account, id=account_pk)

    begin_year = int(begin_date[0:4])
    begin_month = int(begin_date[4:6])
    begin_day = int(begin_date[6:8])
    end_year = int(end_date[0:4])
    end_month = int(end_date[4:6])
    end_day = int(end_date[6:8])
    begin_date = date(year=begin_year, month=begin_month, day=begin_day)
    end_date = date(year=end_year, month=end_month, day=end_day)
    end_date = min(end_date, date.today())

    jelis = list(JournalEntryLineItem.objects.filter(
        account=account_pk,
        journal_entry__when__gte=begin_date,
        journal_entry__when__lte=end_date,
    ))

    jelis.sort(key=lambda x: x.journal_entry.when)

    jelis_with_total = []
    start_balance = Decimal("0.00")
    running_total = start_balance
    for jeli in jelis:
        jeli.sign = Decimal("+1") if jeli.action == jeli.ACTION_BALANCE_INCREASE else Decimal("-1")
        running_total += jeli.sign * jeli.amount
        jeli.total = running_total
        jelis_with_total.append(jeli)

    del jelis

    params = {
        'acct': acct,
        'start_balance': start_balance,
        'jelis': jelis_with_total,
    }
    return render(request, 'books/account-history.html', params)
