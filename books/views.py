
# Standard
from datetime import date, datetime, timedelta
from logging import getLogger
from typing import List
import json
from decimal import Decimal
from typing import Optional
from urllib.parse import urlsplit

# Third Party
from django.shortcuts import render
from rest_framework import viewsets
from django.http.response import HttpResponse
from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
import requests
from numpy import array

# import numpy as np
# from dateutil.parser import parse

# Local
from .models import (
    Account, ACCT_ASSET_CASH,
    BankAccountBalance,
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

ONE_DAY = timedelta(days=1)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def _grp(pts):
    """ Grouping aggregator """
    curr_x = None
    y_sum = 0
    pts.sort(key=lambda pt: pt[0])
    for pt in pts:
        if curr_x is None:
            curr_x = pt[0]
        if curr_x != pt[0]:
            yield [curr_x, y_sum]
            curr_x = pt[0]
            y_sum = 0
        y_sum += pt[1]


def _acc(pts):
    """ Accumulates """
    acc_vs_time = []
    acc_to_date = 0.0
    for pt in _grp(pts):
        acc_to_date += pt[1]
        yield [pt[0], acc_to_date]


def _fill(pts):
    """ Interpolator that uses most recent previous value """
    prev_pt = None
    for pt in pts:
        if prev_pt is None:
            prev_pt = pt
        while prev_pt[0] < pt[0]-ONE_DAY:
            prev_pt = [prev_pt[0]+ONE_DAY, prev_pt[1]]
            yield prev_pt
        yield pt
        prev_pt = pt


def _shift(amount:float, pts):
    """ Shifts all y values up or down """
    for pt in pts:
        yield [pt[0], pt[1]+amount]


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

@login_required
def cashonhand_vs_time_chart(request):

    # TODO: Turn this into a @directors_only decorator that uses @login_required
    # REVIEW: This creates a dependency on "members". Review members/books relationship.
    if not request.user.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")

    start = date(2016, 9, 12)
    end = date.today()

    root_cash_acct = Account.get(ACCT_ASSET_CASH)
    cash_accts = filter(
        lambda x: x.is_subaccount_of(root_cash_acct) or x == root_cash_acct,
        Account.objects.all()
    ) # type: List[Account]
    cash_acct_ids = map(
        lambda x: x.id,
        cash_accts
    ) # type: List[int]

    cash_jelis = JournalEntryLineItem.objects.filter(
      account_id__in=cash_acct_ids,
      journal_entry__when__gte=start,
      journal_entry__when__lte=end
    ).prefetch_related('journal_entry')

    cash_deltas = []
    for jeli in cash_jelis:  # type: JournalEntryLineItem
        if jeli.action == JournalEntryLineItem.ACTION_BALANCE_DECREASE:
            pt = [jeli.journal_entry.when, -1.0*float(jeli.amount)]
        else:
            pt = [jeli.journal_entry.when, 1.0*float(jeli.amount)]
        cash_deltas.append(pt)
    cash_pts = list(_fill(_acc(cash_deltas)))

    bank_pts = map(
        lambda bal: [bal.when, float(bal.balance)],
        BankAccountBalance.objects.filter(
            when__gte=start,
            when__lte=end,
            order_on_date=0,
        ).order_by("when")
    )
    bank_pts = list(_fill(bank_pts))

    # Fit cash points to bank points:
    n = min(len(bank_pts), len(cash_pts))
    assert cash_pts[0][0] == bank_pts[0][0]
    assert cash_pts[n-1][0] == bank_pts[n-1][0]
    bs = array([y for [x, y] in bank_pts[0:n]])
    cs = array([y for [x, y] in cash_pts[0:n]])
    sumofsq_min = None
    optimal_offset = None
    for i in range(n):
        offset = bs[i]-cs[i]
        residuals = (bs - (cs + offset))
        sumofsq = (sum(residuals*residuals))
        if sumofsq_min is None or sumofsq < sumofsq_min:
            sumofsq_min = sumofsq
            optimal_offset = offset

    params = {
        'cash': _shift(optimal_offset, cash_pts),
        'bank': bank_pts
    }
    return render(request, 'books/cashonhand-vs-time-chart.html', params)

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
        _logger.error("Couldn't get purchase info from SquareUp.")
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
def account_history(
    request,
    account_pk: int,
    begin_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    acct = get_object_or_404(Account, id=account_pk)

    now = timezone.localtime(timezone.now())

    if begin_date is None:
        begin_year = now.year-1
        begin_month = now.month
        begin_day = now.day
    else:
        begin_year = int(begin_date[0:4])
        begin_month = int(begin_date[4:6])
        begin_day = int(begin_date[6:8])

    if end_date is None:
        end_year = now.year
        end_month = now.month
        end_day = now.day
    else:
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

    decrease_total = Decimal("0.00")
    increase_total = Decimal("0.00")
    for jeli in jelis:  # type: JournalEntryLineItem
        je = jeli.journal_entry  # type: JournalEntry
        if jeli.action == jeli.ACTION_BALANCE_INCREASE:
            increase_total += jeli.amount
            jeli.sign = 1
        else:
            decrease_total += jeli.amount
            jeli.sign = -1
        # DB contains abs URLs pointing to production, so I'll add relative urls.
        je.relative_source_url = urlsplit(je.source_url).path

    params = {
        'begin_date': begin_date,
        'end_date': end_date,
        'acct': acct,
        'jelis': jelis,
        'decrease_total': decrease_total,
        'increase_total': increase_total,
        'change_total': increase_total - decrease_total,
    }
    return render(request, 'books/account-history.html', params)
