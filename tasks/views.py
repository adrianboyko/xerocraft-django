
# Standard
from hashlib import md5
from datetime import date, datetime, timedelta
import logging
import json
from typing import Generator, Tuple
import calendar

# Third Party
from dateutil.parser import parse  # python-dateutil in requirements.txt
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.template import loader, Context
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from icalendar import Calendar, Event

# Local
from tasks.forms import Desktop_TimeSheetForm
from tasks.models import Task, Nag, Claim, Work, WorkNote, Worker, TimeWindowedObject
from members.models import Member, VisitEvent


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

_logger = logging.getLogger("tasks")

_ORG_NAME_POSSESSIVE = settings.XEROPS_ORG_NAME_POSSESSIVE


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
    return render(request, "tasks/kiosk_task_details.html", {'task': task, 'notes':task.notes.all()})


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
    if task.is_fully_claimed():
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
        if task.is_fully_claimed() and task.all_claims_verified():
            _add_event(cal, task, request)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def ops_calendar_provisional(request) -> HttpResponse:
    """A calendar containing provisionally staffed (i.e. claims not yet verified) tasks."""
    cal = _new_calendar("{} Provisionally Staffed Tasks".format(_ORG_NAME_POSSESSIVE))
    for task in _gen_all_tasks():  # type: Task
        if task.is_fully_claimed() and not task.all_claims_verified():
            _add_event(cal, task, request)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def ops_calendar_unstaffed(request) -> HttpResponse:
    """A calendar containing tasks that are not even provisionally staffed."""
    cal = _new_calendar("{} Unstaffed Tasks".format(_ORG_NAME_POSSESSIVE))
    for task in _gen_all_tasks():  # type: Task
        if not task.is_fully_claimed():
            _add_event(cal, task, request)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def _ops_calendar_json(request, year, month):

    # Python standard libs include the ability to produce padded calendars for a month:
    cal = calendar.Calendar(firstweekday=6)  # Sunday
    calpage = cal.monthdatescalendar(year, month)
    first_date = calpage[0][0]
    last_date = calpage[-1][-1]
    qset = Task.objects\
        .filter(scheduled_date__gte=first_date, scheduled_date__lte=last_date)\
        .prefetch_related("claim_set")
    page_tasks = list(qset)

    def task_json(task: Task) -> dict:
        window = None
        if task.window_duration() is not None and task.window_start_time() is not None:
            msec_dur = 1000.0 * task.window_duration().total_seconds()
            start_time = task.window_start_time()
            window ={
                "begin": {"hour": start_time.hour, "minute": start_time.minute},
                "duration": msec_dur
            }
        else:
            window = None

        user = request.user
        actions = task.possible_actions_for(user.member) if user.is_authenticated() else []

        staffed_by_names = []
        users_claim = None
        for claim in task.claim_set.all():
            if claim.status == Claim.STAT_CURRENT:
                staffed_by_names.append(claim.claiming_member.friendly_name)
            if user.is_authenticated() and user.member == claim.claiming_member:
                users_claim = claim.pk

        return {
            "taskId": task.pk,
            "isoDate": task.scheduled_date.isoformat(),
            "shortDesc": task.short_desc,
            "timeWindow": window,
            "instructions": task.instructions,
            "staffingStatus": task.staffing_status(),
            "possibleActions": actions,
            "staffedBy": staffed_by_names,
            "taskStatus": task.status,
            "usersClaimId": users_claim,
        }

    def tasks_on_date(x: date):
        task_list_for_date = [t for t in page_tasks if t.scheduled_date == x]
        return {
            "dayOfMonth": x.day,
            "isInTargetMonth": x.month == month,
            "isToday": x == date.today(),
            "tasks":[task_json(t) for t in task_list_for_date]
        }

    user_info = None
    u = request.user
    if u.is_authenticated():
        user_info = {"memberId": u.member.pk, "name": u.member.friendly_name}
    return {
        "user": user_info,
        "tasks": [list(tasks_on_date(day) for day in week) for week in calpage],
        "year": year,
        "month": month,
    }


def ops_calendar_json(request, year=None, month=None) -> JsonResponse:
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month
    year = int(year)
    month = int(month)
    return JsonResponse(_ops_calendar_json(request, year, month))


@ensure_csrf_cookie
def ops_calendar_spa(request, year=date.today().year, month=date.today().month) -> HttpResponse:
    year = int(year)
    month = int(month)
    urls = dict(
        claimList=reverse("task:claim-list"),
        taskList=reverse("task:task-list"),
        memberList=reverse("memb:member-list"),
    )

    props = {
        "urls": json.dumps(urls),
        "cal_data": json.dumps(_ops_calendar_json(request, year, month)),
    }
    return render(request, "tasks/ops-calendar-spa.html", props)


def resource_calendar(request):
    cal = _new_calendar("Xerocraft Resource Usage")
    #for task in Task.objects.all():
    #    if task.scheduled_date is None or task.work_start_time is None or task.work_duration is None:
    #        continue
    #    _add_event(cal,task,request)
    #    # Intentionally lacks ALARM
    return _ical_response(cal)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def _form_to_session(request, form, witness_username):
    request.session['work_desc'] = form.cleaned_data["work_desc"]
    request.session['work_date'] = form.cleaned_data["work_date"].strftime("%m/%d/%Y")
    request.session['work_time'] = form.cleaned_data["work_time"].strftime("%-I:%M %p")
    request.session['work_dur'] = float(form.cleaned_data["work_dur"])
    request.session['witness_username'] = witness_username
    request.session.modified = True


def _session_to_form(request, form):
    form.fields['work_desc'].initial = request.session.get('work_desc', "")
    form.fields['work_date'].initial = request.session.get("work_date", "")
    form.fields['work_time'].initial = request.session.get("work_time", "")
    form.fields['work_dur'].initial = request.session.get("work_dur", "")
    form.fields['witness_id'].initial = request.session.get('witness_username', "")


def _clear_session(request):
    del request.session['work_desc']
    del request.session['work_date']
    del request.session['work_time']
    del request.session['work_dur']
    del request.session['witness_username']
    request.session.modified = True

@login_required
def desktop_timesheet(request):

    if request.method == 'POST':  # Process the form data.
        form = Desktop_TimeSheetForm(request.POST, request=request)
        if form.is_valid():
            witness_id = form.cleaned_data["witness_id"]
            witness_pw = form.cleaned_data["witness_pw"]
            witness = authenticate(username=witness_id, password=witness_pw)
            worker = request.user
            _form_to_session(request, form, witness.username)
            return redirect('task:desktop-timesheet-verify')

    else:  # If a GET (or any other method) we'll create a blank form.
        form = Desktop_TimeSheetForm(request=request)
        _session_to_form(request, form)

    return render(request, 'tasks/desktop_timesheet.html', {'form': form})


@login_required
def desktop_timesheet_verify(request):

    if request.method == 'POST':
        user = request.user  # The worker
        try:
            uncat_claim = Claim.objects.get(
                claiming_member=user.member,
                claimed_task__short_desc="Uncategorized Work-Trade"
            )
            work_date = parse(request.session.get('work_date')).date()
            work_dur = timedelta(hours=float(request.session.get('work_dur')))
            # Decided to include witness in WorkNote instead of being an FK in Work
            # because I couldn't think of a use-case for the latter.
            note = "Started at %s and witnessed by %s. Description: %s" % (
                request.session.get('work_time'),
                request.session.get('witness_username'),
                request.session.get('work_desc'),
            )
            work = Work.objects.create(claim=uncat_claim, work_date=work_date,work_duration=work_dur)
            WorkNote.objects.create(author=user.member, content=note, work=work)
            _clear_session(request)

        except Exception as e:
            return HttpResponse("ERROR "+str(e))

        return HttpResponse("SUCCESS")

    else:  # For GET and any other methods:
        return render(request, 'tasks/desktop_timesheet_verify.html', {})

