from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from tasks.models import Task

from datetime import date


def nudge_info(request, task_pk, auth_token):
    task = get_object_or_404(Task, pk=task_pk)
