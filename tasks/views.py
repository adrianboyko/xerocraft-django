
# Standard
from hashlib import md5
from datetime import date, datetime, timedelta
import logging
import json
from typing import Generator, Tuple, Optional
from decimal import Decimal

# Third Party
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
import django.utils.timezone as timezone
from icalendar import Calendar, Event

# Local
from tasks.models import Task, Nag, Claim, Work, WorkNote, Worker
from members.models import Member


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

_logger = logging.getLogger("tasks")

_ORG_NAME_POSSESSIVE = settings.BZWOPS_ORG_NAME_POSSESSIVE


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# For Nags
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def note_task_done(request, task_pk, auth_token):

    task, nag = _get_task_and_nag(task_pk, auth_token)  # type: Tuple[Task, Nag]

    task.status = Task.STAT_DONE
    task.save()
    # TODO: Should also note work done, but I don't have an immediate need for that.

    finisher = nag.who  # type: Member
    finisher.worker.populate_calendar_token()  # Idempotent

    params = {
        'title': "Done",
        'message': "Thank You!",
        'friendly_name': finisher.friendly_name,
        'cal_token': finisher.worker.calendar_token,
    }

    return render(request, 'tasks/simple-generic-response.html', params)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Nag eligible workers to claim unclaimed tasks
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def _get_task_and_nag(task_pk, auth_token):
    md5str = md5(auth_token.encode()).hexdigest()
    task = get_object_or_404(Task, pk=task_pk)
    nag = get_object_or_404(Nag, auth_token_md5=md5str)
    assert(task in nag.tasks.all())
    return task, nag


def offer_task(request, task_pk, auth_token):

    task, nag = _get_task_and_nag(task_pk, auth_token)

    if request.method == 'POST':
        h = request.POST['hours']
        t = datetime.strptime(h,"%H:%M:%S")

        # TODO: There's some risk that user will end up here via browser history. Catch unique violation exception?
        Claim.objects.update_or_create(
            claimed_task=task,
            claiming_member=nag.who,
            defaults={
                'claimed_start_time': task.work_start_time,
                'claimed_duration': timedelta(hours=t.hour, minutes=t.minute, seconds=t.second),
                'status': Claim.STAT_CURRENT,
                'date_verified': date.today(),
            }
        )
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
            "claims": task.claim_set.filter(status=Claim.STAT_CURRENT),
            "max_hrs_to_claim": task.max_claimable_hours(),
            "auth_token": auth_token,
            "zero": timedelta(0),
        }
        return render(request, 'tasks/offer_task.html', params)


def offer_more_tasks(request, task_pk, auth_token):

    task, nag = _get_task_and_nag(task_pk, auth_token)

    if request.method == 'POST':
        pks = request.POST.getlist('tasks')
        for pk in pks:
            t = Task.objects.get(pk=pk)
            # TODO: There's some risk that user will end up here via browser history. Catch unique violoation exception?
            Claim.objects.update_or_create(
                claimed_task=t,
                claiming_member=nag.who,
                defaults={
                    'claimed_start_time': t.work_start_time,
                    'claimed_duration': t.max_work,
                    'status': Claim.STAT_CURRENT,
                    'date_verified': date.today(),
                }
            )
        return redirect('task:offers-done', auth_token=auth_token)

    else: # GET or other methods:

        all_future_instances = Task.objects.filter(
            recurring_task_template=task.recurring_task_template,
            scheduled_date__gt=task.scheduled_date,
            status=Task.STAT_ACTIVE
        )
        future_instances_same_dow = []
        for instance in all_future_instances:
            if instance.scheduled_weekday() == task.scheduled_weekday() \
               and instance.unclaimed_hours() == instance.max_work \
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


def offers_done(request, auth_token):

    md5str = md5(auth_token.encode()).hexdigest()
    nag = get_object_or_404(Nag, auth_token_md5=md5str)
    member = nag.who
    worker = member.worker
    worker.populate_calendar_token()  # Does nothing if already populated.

    # Return page with a link to the calendar:
    return render(request, 'tasks/offers_done.html', {"worker": worker})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Verify that worker will work auto-claimed task
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def verify_claim(request, task_pk, claim_pk, will_do, auth_token):

    task = get_object_or_404(Task, pk=task_pk)

    md5str = md5(auth_token.encode()).hexdigest()
    nag = get_object_or_404(Nag, auth_token_md5=md5str)
    assert(task in nag.tasks.all())

    claim = get_object_or_404(Claim, pk=claim_pk)
    claimant = claim.claiming_member

    assert nag.who == claimant
    assert(claim in nag.claims.all())

    if will_do == "Y":  # The default claimant verifies they will do the work.
        try:
            # See if there's already a current claim on the task:
            current_claim = Claim.objects.get(claimed_task=task, status=Claim.STAT_CURRENT)  # type: Claim
            # There is a current claim. Does it belong to the user of this view (the person we nagged)?
            if current_claim.claiming_member != nag.who:
                # No, the current claim belongs to somebody else, so we tell the view user about it
                # By redirecting to another view that does so.
                return redirect('task:offer-task', task_pk=task_pk, auth_token=auth_token)

        except Claim.DoesNotExist:
            # There's no current claim, so nothing to worry about.
            pass

        claim.date_verified = date.today()
        claim.status = Claim.STAT_CURRENT
        claim.save()

    elif will_do == "N":  # The default claimant says they can't do the work, this time.
        claim.date_verified = date.today()
        claim.status = Claim.STAT_ABANDONED
        claim.save()

    else:
        raise RuntimeError("Expected Y or N parameter.")

    claimant.worker.populate_calendar_token()  # Idempotent

    params = {
        'claimant_friendly_name': claimant.friendly_name,
        'claim': claim,
        'task': task,
        'dow': task.scheduled_weekday(),
        'auth_token': auth_token,
        'will_do': will_do,
        'cal_token': claimant.worker.calendar_token,
    }
    return render(request, 'tasks/verify-claim-response.html', params)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Task details
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def cal_task_details(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    return render(request, "tasks/cal_task_details.html", {'task': task, 'notes':task.notes.all()})


def kiosk_task_details(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    response = render(request, "tasks/kiosk_task_details.html", {'task': task, 'notes':task.notes.all()})
    return response


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ELM VIEWS FOR NAG CLICKS (Experimental development)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


def offer_task_spa(request, task_pk=0, auth_token=""):
    task, nag = _get_task_and_nag(task_pk, auth_token)

    claims = task.claim_set.filter(status=Claim.STAT_CURRENT)

    if len(claims) == 0:
        claim = None
    else:
        claim = claims[0]

    if len(claims) > 1:
        # Note that I'm not going to offer partial claim functionality in this version of the view.
        _logger.error("Task #{} has more than one claim.", task.pk)

    # ---------------------------------------------------
    # Bundle up info for the task offer
    # ---------------------------------------------------

    task_time_str = str(task.work_duration.total_seconds()/3600.0) + " hr"
    task_time_str += "" if task_time_str == "1" else "s"
    if task.work_start_time is not None:
        task_time_str += " at " + task.work_start_time.strftime("%I:%M %p")

    futures = task.all_future_instances_same_dow()
    futures = [x for x in futures if len(x.claim_set.all()) == 0]
    futures = [x for x in futures if nag.who in x.all_eligible_claimants()]
    futures = sorted(futures, key=lambda x: x.scheduled_date)
    futures = [x.pk for x in futures]

    nag.who.worker.populate_calendar_token()

    task_data = {
        "auth_token": auth_token,
        "task_id": task.pk,
        "user_friendly_name": nag.who.friendly_name,
        "nagged_member_id": nag.who.pk,
        "task_desc": task.short_desc,
        "task_day_str": task.scheduled_date.strftime("%A, %b %e"),
        "task_window_str": task_time_str,

        "task_work_start_str": str(task.work_start_time),
        "task_work_dur_str": str(task.work_duration),

        "already_claimed_by": claim.claiming_member.friendly_name if claim is not None else "",
        "future_task_ids": futures[0:4],
        "calendar_url": reverse('task:member-calendar', args=[nag.who.worker.calendar_token]),

        "today_str": str(date.today()),

        "claim_list_uri": reverse("task:claim-list"),
        "task_list_uri": reverse("task:task-list"),
        "member_list_uri": reverse("memb:member-list"),
    }

    props = {
        "task_data": json.dumps(task_data),
    }

    return render(request, "tasks/offer-task-spa.html", props)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def verify_claim_spa(request, claim_pk=0, auth_token=""):

    claim = get_object_or_404(Claim, pk=claim_pk)
    task = claim.claimed_task
    who = claim.claiming_member

    who.worker.populate_calendar_token()

    params = {
    }

    params = json.dumps(params)
    return render(request, "tasks/verify-claim-spa.html", {"props": params})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# KIOSK (Experimental development)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def _get_task_and_member(task_pk, member_card_str):

    try:
        task = Task.objects.get(pk=task_pk)
    except Task.DOES_NOT_EXIST:
        msg = "Info provided doesn't correspond to a task."
        _logger.error(msg)
        return None, None, JsonResponse({"error": msg})

    if task.work_start_time is None or task.work_duration is None:
        msg = "Expected a task with a specific time window."
        _logger.error(msg)
        return None, None, JsonResponse({"error": msg})

    member = Member.get_by_card_str(member_card_str)
    if member is None:
        # This might legitimately occur if an invalidated card is presented at the kiosk.
        msg = "Info provided doesn't correspond to a member."
        _logger.warning(msg)
        return None, None, JsonResponse({"error": msg})

    return task, member, None


def will_work_now(request, task_pk, member_card_str):
    """ User says they'll work a certain task starting immediately (or at task start time).
        Claim the task if it isn't already claimed. Set claim to WORKING status.
    """
    # TODO: Move this logic to Task or Claim model?

    task, member, response = _get_task_and_member(task_pk, member_card_str)
    if response is not None: return response

    if member in task.claimants.all():
        # Following get won't raise exception because we already know the claim exists.
        claim = Claim.objects.get(claimed_task=task, claiming_member=member)
        if claim.status == Claim.STAT_CURRENT:
            # TODO: Adjust claimed_start_time and duration if task has already started.
            claim.status = Claim.STAT_WORKING
            claim.save()
            return JsonResponse({"success": "Existing claim was set to WORKING status."})
        elif claim.status == Claim.STAT_WORKING:
            return JsonResponse({"success": "You were already marked as working this task."})
        else:
            # There's an extremely small chance that multiuser activity will get us here:
            return JsonResponse({"error": "You can't work this task."})

    # If there are multiple kiosks/apps running, it's possible that somebody else took this task
    # while member was considering whether or not to claim it. Check to see.
    if task.is_fully_claimed:
        # This message doesn't need to be logged since it's an expected error.
        return JsonResponse({"error": "Looks like somebody else just claimed it, so you can't."})

    if member not in task.all_eligible_claimants():
        # There is a small chance that this will happen legitimately, so I'll call it a warning.
        msg = "You aren't eligible to claim this task."
        logging.getLogger("tasks").warning(msg)
        return JsonResponse({"error": msg})

    claim = Claim.objects.create(
        claimed_task=task,
        claiming_member=member,
        claimed_start_time=task.work_start_time,
        claimed_duration=task.work_duration,
        status=Claim.STAT_WORKING,
        date_verified=date.today(),
    )
    return JsonResponse({"success": "A new claim was created and set to WORKING status."})


def record_work(request, task_pk, member_card_str):

    task, member, response = _get_task_and_member(task_pk, member_card_str)
    if response is not None: return response

    if member not in task.claimants.all():
        msg = "You are not working on this task."
        _logger.error(msg)
        return JsonResponse({"error": msg})

    claim = Claim.objects.get(claimed_task=task, claiming_member=member)
    if claim.status != Claim.STAT_WORKING:
        msg = "You are not working on this task."
        _logger.error(msg)
        return JsonResponse({msg})

    #TODO: Create a work entry. Should probably give worker a chance to edit hours.

    """ TODO:
        If task (is not windowed) OR (is windowed and is inside window):
            Ask worker if they are done with this task or if they'll be returning to it.
            If done, set claim status to DONE and ask if task is done.
               If task is done, set task status to DONE
        else:
            # task is windowed AND is outside window.
            Set claim status to DONE
            Set task status to DONE
        return a response with task and claim info.
    """

    return JsonResponse({"success": "The task has been marked as done.\nWe appreciate your help!"})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CALENDARS
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

AZ_TIMEZONE = '''BEGIN:VTIMEZONE
TZID:America/Phoenix
X-LIC-LOCATION:America/Phoenix
BEGIN:STANDARD
TZOFFSETFROM:-0700
TZOFFSETTO:-0700
TZNAME:MST
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE
'''


def _new_calendar(name):
    cal = Calendar()
    cal['x-wr-calname'] = name
    cal['version'] = "2.0"
    cal['calscale'] = "GREGORIAN"
    cal['method'] = "PUBLISH"
    tz = cal.from_ical(AZ_TIMEZONE)
    cal.add_component(tz)
    return cal


def _add_event(cal, task: Task, request):

    # NOTE: We could add task workers as attendees, but the calendar format insists that these
    # be email addresses and we don't want to expose personal information about the workers.
    # So we'll build a worker string and make it part of the event description.
    worker_str = ""
    for claim in task.claim_set.filter(status__in=[Claim.STAT_CURRENT, Claim.STAT_WORKING],):  # type: Claim
        worker_str += ", " if worker_str else ""
        worker_str += claim.claiming_member.friendly_name
    if not worker_str:
        worker_str = "Nobody has claimed this task."

    desc_str = task.instructions.replace("\r\n", "\\N")  # don't try \\n

    dtstart = datetime.combine(task.scheduled_date, task.work_start_time)
    relpath = reverse('task:cal-task-details', args=[task.pk])
    event = Event()
    event.add('uid',         task.pk)
    event.add('url',         request.build_absolute_uri(relpath))
    event.add('summary',     task.short_desc)
    event.add('description', "Who: {}\\N\\N{}".format(worker_str, desc_str))
    event.add('dtstart',     dtstart)
    event.add('dtend',       dtstart + task.work_duration)
    event.add('dtstamp',     datetime.now())
    cal.add_component(event)


def _ical_response(cal):
    ics = cal.to_ical()
    response = HttpResponse(ics, content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename="calendar.ics"'
    # TODO: No cache header?
    return response


def _gen_tasks_for(member):
    """For the given member, generate all future tasks and past tasks in last 60 days"""
    for task in member.tasks_claimed.filter(scheduled_date__gte=datetime.now()-timedelta(days=60)):  # type: Task
        if task.scheduled_date is None or task.work_start_time is None or task.work_duration is None:
            continue
        yield task


def _gen_all_tasks() -> Generator[Task, None, None]:
    """Generate all future tasks and past tasks in last 60 days"""

    qset = Task.objects\
        .filter(scheduled_date__gte=datetime.now()-timedelta(days=60))\
        .prefetch_related("claim_set")

    for task in qset:  # type: Task
        if task.scheduled_date is None or task.work_start_time is None or task.work_duration is None:
            continue
        yield task


def member_calendar(request, token):

    # See if token corresponds to a Worker's calendar_token:
    try:
        worker = Worker.objects.get(calendar_token=token)
        member = worker.member
    except Worker.DoesNotExist:
        member = None

    # If token didn't correspond to nag, see if it's a member card string:
    if member is None:
        member = Member.get_by_card_str(token)

    if member is None:
        raise Http404("No such calendar")

    cal = _new_calendar("My Xerocraft Tasks")
    for task in _gen_tasks_for(member):  # type: Task
        _add_event(cal, task, request)
        # TODO: Add ALARM
    return _ical_response(cal)


def ops_calendar(request):
    cal = _new_calendar("All {} Tasks".format(_ORG_NAME_POSSESSIVE))
    for task in _gen_all_tasks():  # type: Task
        _add_event(cal, task, request)
        # Intentionally lacks ALARM
    return _ical_response(cal)


def ops_calendar_staffed(request) -> HttpResponse:
    """A calendar containing tasks that have been verified as staffed."""
    cal = _new_calendar("{} Staffed Tasks".format(_ORG_NAME_POSSESSIVE))
    for task in _gen_all_tasks():  # type: Task
        if task.is_fully_claimed and task.all_claims_verified():
            _add_event(cal, task, request)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def ops_calendar_provisional(request) -> HttpResponse:
    """A calendar containing provisionally staffed (i.e. claims not yet verified) tasks."""
    cal = _new_calendar("{} Provisionally Staffed Tasks".format(_ORG_NAME_POSSESSIVE))
    for task in _gen_all_tasks():  # type: Task
        if task.is_fully_claimed and not task.all_claims_verified():
            _add_event(cal, task, request)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def ops_calendar_unstaffed(request) -> HttpResponse:
    """A calendar containing tasks that are not even provisionally staffed."""
    cal = _new_calendar("{} Unstaffed Tasks".format(_ORG_NAME_POSSESSIVE))
    for task in _gen_all_tasks():  # type: Task
        if not task.is_fully_claimed:
            _add_event(cal, task, request)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def resource_calendar(request):
    cal = _new_calendar("Xerocraft Resource Usage")
    #for task in Task.objects.all():
    #    if task.scheduled_date is None or task.work_start_time is None or task.work_duration is None:
    #        continue
    #    _add_event(cal,task,request)
    #    # Intentionally lacks ALARM
    return _ical_response(cal)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# This is still required because it launches the Elm client.
@ensure_csrf_cookie
def ops_calendar_spa(request, year=date.today().year, month=date.today().month) -> HttpResponse:
    year = int(year)
    month = int(month)

    props = {
        "year": year,
        "month": month
    }
    return render(request, "tasks/ops-calendar-spa.html", props)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def desktop_timesheet(request):
    # This has been stubbed out with a notice that this form has been retired.
    # REVIEW: Change was made on 1Feb2018. View be removed after some time.
    return render(request, 'tasks/desktop_timesheet.html', {})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

from tasks.models import TimeAccountEntry
from django.contrib.auth.models import User
from collections import OrderedDict

@login_required
def time_acct_statement(request, range:str):
    user = request.user  # type: User

    # TODO: Need to drive creation of expirations more sensibly.
    TimeAccountEntry.regenerate_expirations(user.member.worker)

    statement_start_datetime = timezone.now()  # type: datetime
    if range == "all":
        statement_start_datetime -= timedelta(days=365*20)  # A long time ago.
        subtitle = "for all time"
    if range == "recent":
        statement_start_datetime -= timedelta(days=90)  # The rollover limit.
        subtitle = "last 90 days"
    lines = TimeAccountEntry.objects.filter(
        worker=user.member.worker,
        when__gte=statement_start_datetime
    ).order_by('when')

    if len(lines) > 0:
        balance_forward = lines[0].balance - lines[0].change
    else:
        balance_forward = Decimal("0.00")
    balance = balance_forward
    for line in lines:
        balance += line.change
        line.bal = balance

    args = {
        'user': user,
        'balance_forward': balance_forward,
        'decimalzero': Decimal("0.00"),
        'lines': lines,
        'subtitle': subtitle
    }
    return render(request, 'tasks/time-acct-statement.html', args)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# from rest_framework.schemas import get_schema_view
# from rest_framework import renderers
# from openapi_codec import OpenAPICodec
#
#
# class SwaggerRenderer(renderers.BaseRenderer):
#     media_type = 'application/openapi+json'
#     format = 'swagger'
#
#     def render(self, data, media_type=None, renderer_context=None):
#         codec = OpenAPICodec()
#         return codec.dump(data)
#
#
# schema_view = get_schema_view(
#     title="Tasks API",
#     urlconf="tasks.urls",
#     renderer_classes=[SwaggerRenderer],
# )

