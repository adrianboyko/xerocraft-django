from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import hashlib
from tasks.models import Task, Nag, Claim

from datetime import date


def _get_task_and_nag(task_pk, auth_token):
    md5 = hashlib.md5(auth_token.encode()).hexdigest()
    task = get_object_or_404(Task, pk=task_pk)
    nag = get_object_or_404(Nag, auth_token_md5=md5)
    assert(task in nag.tasks.all())
    return task, nag


def offer_task(request, task_pk, auth_token):

    task, nag = _get_task_and_nag(task_pk, auth_token)

    # TODO: Is task closed?
    # TODO: Is task fully claimed?
    # TODO: Is task scheduled in the past?
    # TODO: Is member still eligible to work the task?

    params = {
        "task": task,
        "member": nag.who,
        "dow": task.scheduled_weekday(),
        "claims": task.claim_set.filter(status=Claim.CURRENT),
        "max_hrs_to_claim": float(min(task.unclaimed_hours(), task.duration())),
        "auth_token": auth_token
    }
    return render(request, 'tasks/offer_task.html', params)


def claim_task(request, task_pk, auth_token, hours):

    task,nag = _get_task_and_nag(task_pk, auth_token)
    Claim.objects.create(task=task, member=nag.who, hours_claimed=hours, status=Claim.CURRENT)
    return redirect('task:offer-more-tasks', task_pk=task_pk, auth_token=auth_token)


def offer_more_tasks(request, task_pk, auth_token):

    task, nag = _get_task_and_nag(task_pk, auth_token)

    future_instances_same_dow = []
    all_future_instances = Task.objects.filter(
        recurring_task_template = task.recurring_task_template,
        scheduled_date__gt = task.scheduled_date,
        work_done = False
    )

    for instance in all_future_instances:
        max_hours_to_claim = float(min(instance.unclaimed_hours(), instance.duration()))
        if instance.scheduled_weekday() == task.scheduled_weekday() and \
           max_hours_to_claim > 0 and \
           nag.who in instance.all_eligible_claimants():
            future_instances_same_dow.append(instance)

    params = {
        "task": task,
        "member": nag.who,
        "dow": task.scheduled_weekday(),
        "instances": future_instances_same_dow,
    }
    return render(request, 'tasks/offer_more_tasks.html', params)
