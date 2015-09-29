from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse, Http404
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from hashlib import md5
from datetime import date, datetime

from tasks.models import Task, Nag, Claim, CalendarSettings
from members.models import Member

from icalendar import Calendar, Event


def _get_task_and_nag(task_pk, auth_token):
    md5str = md5(auth_token.encode()).hexdigest()
    task = get_object_or_404(Task, pk=task_pk)
    nag = get_object_or_404(Nag, auth_token_md5=md5str)
    assert(task in nag.tasks.all())
    return task, nag


def offer_task(request, task_pk, auth_token):

    task, nag = _get_task_and_nag(task_pk, auth_token)

    if request.method == 'POST':
        hours = request.POST['hours']
        # TODO: There's some risk that user will end up here via browser history. Catch unique violoation exception?
        Claim.objects.create(task=task, member=nag.who, hours_claimed=hours, status=Claim.CURRENT)
        return redirect('task:offer-more-tasks', task_pk=task_pk, auth_token=auth_token)

    else:  # GET and other methods

        # TODO: Is task closed?
        # TODO: Is task fully claimed?
        # TODO: Is task scheduled in the past?
        # TODO: Is member still eligible to work the task?
        # TODO: Is member already scheduled for another task in this time slot?

        params = {
            "task": task,
            "member": nag.who,
            "dow": task.scheduled_weekday(),
            "claims": task.claim_set.filter(status=Claim.CURRENT),
            "max_hrs_to_claim": float(min(task.unclaimed_hours(), task.duration.seconds/3600.0)),
            "auth_token": auth_token
        }
        return render(request, 'tasks/offer_task.html', params)


def offer_more_tasks(request, task_pk, auth_token):

    task, nag = _get_task_and_nag(task_pk, auth_token)

    if request.method == 'POST':
        pks = request.POST.getlist('tasks')
        for pk in pks:
            t = Task.objects.get(pk=pk)
            # TODO: There's some risk that user will end up here via browser history. Catch unique violoation exception?
            Claim.objects.create(task=t, member=nag.who, hours_claimed=t.duration.seconds/3600.0, status=Claim.CURRENT)
        return redirect('task:offers-done', auth_token=auth_token)

    else: # GET or other methods:

        all_future_instances = Task.objects.filter(
            recurring_task_template=task.recurring_task_template,
            scheduled_date__gt=task.scheduled_date,
            work_done=False
        )
        future_instances_same_dow = []
        for instance in all_future_instances:
            if instance.scheduled_weekday() == task.scheduled_weekday() \
               and instance.unclaimed_hours() == instance.work_estimate \
               and nag.who in instance.all_eligible_claimants():
                future_instances_same_dow.append(instance)
            if len(future_instances_same_dow) > 3:  # Don't overwhelm potential worker.
                break

        if len(future_instances_same_dow) > 0:
            params = {
                "task": task,
                "member": nag.who,
                "dow": task.scheduled_weekday(),
                "instances": future_instances_same_dow,
                "auth_token": auth_token,
            }
            return render(request, 'tasks/offer_more_tasks.html', params)
        else:  # There aren't any future instances of interest so we're done"
            return redirect('task:offers-done', auth_token=auth_token)


def offers_done(request, token):

    # See if token corresponds to a nag and get member from there, if it is.
    md5str = md5(token.encode()).hexdigest()
    try:
        nag = Nag.objects.get(auth_token_md5=md5str)
        member = nag.who
    except Nag.DoesNotExist:
        member = None

    # If token didn't correspond to nag, see if it's a member card string:
    if member is None:
        member = Member.get_by_card_str(token)

    if member is None:
        raise Http404("No such calendar")

    # Get the member's calendar settings, or create them if they don't exist:
    try:
        settings = CalendarSettings.objects.get(who=member)
    except CalendarSettings.DoesNotExist:
        # I'm arbitrarily choosing md5str, below, but the fact that it came from md5 doesn't matter.
        _, md5str = Member.generate_auth_token_str(
            lambda token: CalendarSettings.objects.filter(token=token).count() == 0  # uniqueness test
        )
        settings = CalendarSettings.objects.create(who=member, token=md5str)

    # Return page with a link to the calendar:
    return render(request, 'tasks/offers_done.html', {"member": member, "settings": settings})


def task_details(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    return render(request, "tasks/task_details.html", {'task': task})


def _new_calendar(name):
    cal = Calendar()
    cal['x-wr-calname'] = name
    cal['version'] = "2.0"
    cal['calscale'] = "GREGORIAN"
    cal['method'] = "PUBLISH"
    return cal


def _add_event(cal, task):
    dtstart = datetime.combine(task.scheduled_date, task.start_time)
    event = Event()
    event.add('uid',         task.pk)
    event.add('url',         "http://xerocraft-django.herokuapp.com/tasks/task-details/%d/" % task.pk)
    event.add('summary',     task.short_desc)
    event.add('description', task.instructions.replace("\r\n", " "))
    event.add('dtstart',     dtstart)
    event.add('dtend',       dtstart + task.duration)
    event.add('dtstamp',     datetime.now())
    cal.add_component(event)


def _ical_response(cal):
    ics = cal.to_ical()
    response = HttpResponse(ics, content_type='text/calendar')
    # TODO: Add filename?
    return response


def member_calendar(request, token):  #TODO: Generalize to all users.
    member = Member.objects.get(auth_user__username='adrianb')
    cal = _new_calendar("My Xerocraft Tasks")
    for task in member.tasks_claimed.all():
        if task.scheduled_date is None or task.start_time is None or task.duration is None:
            continue
        _add_event(cal,task)
        #TODO: Add ALARM
    return _ical_response(cal)


def xerocraft_calendar(request):
    cal = _new_calendar("All Xerocraft Tasks")
    for task in Task.objects.all():
        if task.scheduled_date is None or task.start_time is None or task.duration is None:
            continue
        if task.short_desc == "Open Xerocraft" or task.short_desc == "Close Xerocraft":
            continue
        _add_event(cal,task)
        # Intentionally lacks ALARM
    return _ical_response(cal)


def resource_calendar(request):
    cal = _new_calendar("Xerocraft Resource Usage")
    #for task in Task.objects.all():
    #    if task.scheduled_date is None or task.start_time is None or task.duration is None:
    #        continue
    #    _add_event(cal,task)
    #    # Intentionally lacks ALARM
    return _ical_response(cal)

