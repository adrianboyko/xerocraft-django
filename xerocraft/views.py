from django.shortcuts import render
from django.contrib import auth
__author__ = 'Adrian'


def index(request):
    auth.logout(request)  # Helps protect against people who forget to log out.
    return render(request, 'xerocraft/xerocraft-home.html',{})