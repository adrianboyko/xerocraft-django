from django.shortcuts import render, render_to_response
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from members.models import Member

__author__ = 'Adrian'


def index(request):
    return render(request, 'xerocraft/xerocraft-home.html',{})


@login_required
def director_menu(request):
    if not request.user.member.is_tagged_with("Director"):
        return HttpResponse("This page is for Directors only.")
    else:
        return render(request, 'xerocraft/director-menu.html',{})


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
        return render_to_response('xerocraft/login.html', {'next': request.GET.get('next')}, context)


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")
