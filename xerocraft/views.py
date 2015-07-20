__author__ = 'Adrian'

from django.shortcuts import render

def index(request):
    return render(request, 'xerocraft/xerocraft-home.html',{})