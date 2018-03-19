# Standard
import time
from typing import Optional
from logging import getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL
import json

# Third Party
from django.core.management import call_command
from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import RequestContext, loader, Template
from rest_framework.authtoken.models import Token
from rq import Queue
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.authentication import TokenAuthentication

# Local
from members.models import Membership, VisitEvent, ExternalId
from bzw_ops.worker import conn

__author__ = 'Adrian'

logger = getLogger("bzw_ops")

# REVIEW: What is the best place to create the asynch task queue?
q = Queue(connection=conn)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# XIS WEBSITE PAGES
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def index(request):
    return render(request, 'bzw_ops/xerocraft-home.html', {})


def credits(request):
    return render(request, 'bzw_ops/credits.html', {})


@login_required
def accounting_menu(request):
    if not request.user.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")
    else:
        return render(request, 'bzw_ops/accounting-menu.html', {})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# LOGIN / LOGOUT
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# Based on code from http://www.tangowithdjango.com/book/chapters/login.html
def login(request):

    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']
        next = request.POST['next']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = auth.authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                auth.login(request, user)
                return HttpResponseRedirect(next)
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            # return HttpResponse("Invalid login details supplied.")
            return HttpResponseRedirect('.?next='+next)

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        t = loader.get_template('bzw_ops/login.html')  # type:Template
        context = {'next': request.GET.get('next')}
        http = t.render(context=context, request=request)
        return HttpResponse(http)


def logout(request):
    auth.logout(request)
    next = request.GET.get('next', "/")
    return HttpResponseRedirect(next)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# XEROCRAFT.ORG
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# TODO: This is not generic functionality. Move to XIS.

def api_get_membership_info(request, provider: str, uid: str) -> HttpResponse:
    """
    This allows the Xerocraft.org website to query Django's more-complete membership info.
    :param request: The http request
    :param provider: Some value from members_externalid's provider column.
    :param uid: Some value from members_externalid's uid column.
    :return: JSON dict or 401 or 403. JSON dict will include 'current':T/F on success else 'error':<msg>.
    """

    try:
        token_str = request.META['HTTP_AUTHORIZATION'].strip()
    except KeyError:
        return HttpResponse('Authentication failed', status=401)
    if token_str is None or len(token_str) == 0:
        return HttpResponse('Authentication failed', status=401)
    if not token_str.startswith("Token "):
        return HttpResponse('Authentication failed', status=401)

    token_key = token_str.replace("Token ","")
    try:
        token_row = Token.objects.get(key=token_key)
    except Token.DoesNotExist:
        return HttpResponse('Authentication failed', status=401)
    if (not token_row.user.is_staff) or (not token_row.user.is_active):
        return HttpResponse('User not authorized', status=403)

    try:
        social_auth = ExternalId.objects.get(provider=provider, uid=uid)
    except ExternalId.DoesNotExist:
        return JsonResponse({
            'provider': provider,
            'uid': uid,
            'error': "{}/{} does not exist.".format(provider, uid)
        })

    member = social_auth.user.member

    # The following is only meaningful for 'xerocraft.org' provider.
    # I don't anticipate this view being called for other providers.
    # If this view IS called for other providers, username will be None.
    username = social_auth.extra_data.get("User name", None)  # This will be None for some providers.

    try:
        latest_pm = Membership.objects.filter(member=member).latest('start_date')
        json = {
            'provider': provider,
            'uid': uid,
            'username': username,
            'current': member.is_currently_paid(),
            'start-date': latest_pm.start_date,
            'end-date': latest_pm.end_date,
        }
    except Membership.DoesNotExist:
        json = {
            'provider': provider,
            'uid': uid,
            'current': False,
        }
    return JsonResponse(json)


def scrape_checkins():

    def getmax() -> Optional[VisitEvent]:
        try:
            return VisitEvent.objects.latest('when')
        except VisitEvent.DoesNotExist:
            return None

    prevmax = getmax()

    # Scrape a new check-in. Try up to 16 times.
    for i in range(16):
        time.sleep(1)
        call_command("scrapecheckins")
        newmax = getmax()
        if prevmax is None:
            if newmax is not None:
                return
        elif newmax is not None:  # prevmax and newmax are both not None
            if newmax.when > prevmax.when:
                return


def scrape_xerocraft_org_checkins(request) -> JsonResponse:
    result = q.enqueue(scrape_checkins)
    return JsonResponse({'result': "success"})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# TEST URL FOR MONITORING SERVICE(S)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def test(request) -> JsonResponse:
    """Run various quick sanity tests for the uptime monitor."""

    # This is an arbitrary database operation. It will throw an exception if the database
    # is not running, database connection limit has been reached, etc.
    try:
        Membership.objects.latest('start_date')
    except Membership.DoesNotExist:
        pass
    return JsonResponse({'result': "success"})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# OTHER
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def paypal_webhook(request):
    # Not yet sure what the proper response is. This "OK" response is for testing purposes.
    return HttpResponse("OK")


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# LOGGING
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

level_map = {
    "D": DEBUG,
    "I": INFO,
    "W": WARNING,
    "E": ERROR,
    "C": CRITICAL
}


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdminUser])
def log_message(request) -> HttpResponse:
    """ Log a message to the server's logs. """

    if request.method != 'POST':
        return HttpResponse(status=405, data="Method was not POST.")

    data = json.loads(request.body.decode())
    logger_name = data['logger_name']  # type: str
    log_level_str = data['log_level']  # type: str
    msg_to_log = data['msg_to_log']  # type: str

    logger = getLogger(logger_name)
    log_level = level_map[log_level_str]
    logger.log(log_level, msg_to_log)
    return HttpResponse("Success")
