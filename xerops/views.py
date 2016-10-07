# Standard
import time

# Third Party
from django.core.management import call_command
from django.shortcuts import render, render_to_response
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import RequestContext
from social.apps.django_app.default.models import UserSocialAuth
from rest_framework.authtoken.models import Token
from rq import Queue

# Local
from members.models import Membership
from xerops.worker import conn

__author__ = 'Adrian'


def index(request):
    return render(request, 'xerops/xerocraft-home.html',{})


def credits(request):
    return render(request, 'xerops/credits.html',{})


@login_required
def director_menu(request):
    if not request.user.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")
    else:
        return render(request, 'xerops/director-menu.html',{})


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
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('xerops/login.html', {'next': request.GET.get('next')}, context)


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")


def api_get_membership_info(request, provider: str, id: str) -> HttpResponse:
    """
    This allows the Xerocraft.org website to query Django's more-complete membership info.
    :param request: The http request
    :param provider: Some value from social_auth_usersocialauth's provider column.
    :param id: Some value from social_auth_usersocialauth's uid column.
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

    social_auth = UserSocialAuth.objects.get_social_auth(provider, id)
    if social_auth is None:
        return JsonResponse({
            'provider': provider,
            'id': id,
            'error': "{}/{} does not exist.".format(provider, id)
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
            'id': id,
            'username': username,
            'current': member.is_currently_paid(),
            'start-date': latest_pm.start_date,
            'end-date': latest_pm.end_date,
        }
    except Membership.DoesNotExist:
        json = {
            'provider': provider,
            'id': id,
            'current': False,
        }
    return JsonResponse(json)


# REVIEW: What is the best place to create the queue?
q = Queue(connection=conn)


def scrape_checkins():
    for i in range(4):
        call_command("scrapecheckins")
        time.sleep(5)


def scrape_xerocraft_org_checkins(request) -> JsonResponse:
    result = q.enqueue(scrape_checkins)
    return JsonResponse({'result': "success"})


def test(request) -> JsonResponse:
    """Run various quick sanity tests for the uptime monitor."""

    # This is an arbitrary database operation. It will throw an exception if the database
    # is not running, database connection limit has been reached, etc.
    try:
        Membership.objects.latest('start_date')
    except Membership.DoesNotExist:
        pass
    return JsonResponse({'result': "success"})


def paypal_webhook(request):
    # Not yet sure what the proper response is. This "OK" response is for testing purposes.
    return HttpResponse("OK")