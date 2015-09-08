from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import hashlib
from tasks.models import Task, Nag, Claim

from datetime import date


def offer_task(request, task_pk, auth_token):

    md5 = hashlib.md5(auth_token.encode()).hexdigest()

    task = get_object_or_404(Task, pk=task_pk)
    nag = get_object_or_404(Nag, auth_token_md5=md5)
    assert(task in nag.tasks.all())

    # TODO: Is task closed?
    # TODO: Is task fully claimed?
    # TODO: Is task scheduled in the past?
    # TODO: Is member still eligible to work the task?

    params = {
        "task": task,
        "member": nag.who,
        "dow": task.scheduled_weekday(),
        "claims": task.claim_set.filter(status=Claim.CURRENT),
        "max_hrs_to_claim": min(task.unclaimed_hours(), task.duration()),
        "auth_token": auth_token
    }
    return render(request, 'tasks/offer_task.html', params)
