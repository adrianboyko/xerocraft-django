from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.template import loader, Context, RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from tasks.forms import *
from hashlib import md5
from datetime import date, datetime, timedelta
from dateutil.parser import parse
from tasks.models import Task, Nag, Claim, Work, WorkNote, Worker, TimeWindowedObject
from members.models import Member, VisitEvent
from icalendar import Calendar, Event
import logging

# = = = = = = = = = = = = = = = = = = = = KIOSK VISIT EVENT CONTENT PROVIDERS

from members.views import kiosk_visitevent_contentprovider


def task_button_text(obj):
    assert isinstance(obj, TimeWindowedObject)
    desc = obj.window_short_desc()
    if obj.window_start_time() is not None:
        desc += obj.window_start_time().strftime(" @ %H%M")
    return desc


@kiosk_visitevent_contentprovider
def visitevent_arrival_content(member, member_card_str, visit_event_type):

    # Short out if this isn't the event type this contentprovider handles.
    if visit_event_type != VisitEvent.EVT_ARRIVAL: return ""

    working_today = []      # Tasks the member is already working.
    claimed_today = []      # The member's claimed tasks for today
    unclaimed_today = []    # Other tasks scheduled for today that the member could claim
    unclaimed_anytime = []  # Other unscheduled tasks that the member could claim

    # TODO: Don't find tasks that are past their time window.

    halfhour = timedelta(minutes=30)

    # Find member's claimed tasks for today:
    for claim in member.claim_set.filter(
      claimed_task__status=Task.STAT_ACTIVE,
      status__in=[Claim.STAT_CURRENT, Claim.STAT_WORKING],
      claimed_task__scheduled_date=date.today()):
        if not claim.in_window_now(start_leeway=-halfhour): continue
        if claim.status == Claim.STAT_CURRENT:
            claimed_today.append((claim.claimed_task, task_button_text(claim)))
        if claim.status == Claim.STAT_WORKING:
            working_today.append((claim.claimed_task, task_button_text(claim)))

    # Find today's unclaimed tasks:
    for task in Task.objects.filter(status=Task.STAT_ACTIVE, scheduled_date=date.today()):
        if not task.in_window_now(start_leeway=-halfhour): continue
        if member in task.all_eligible_claimants() and task.claimants.count() == 0:
            unclaimed_today.append((task, task_button_text(task)))

    # Find unclaimed tasks with no scheduled date:
    for task in Task.objects.filter(status=Task.STAT_ACTIVE, scheduled_date__isnull=True):
        if not task.in_window_now(start_leeway=-halfhour): continue
        if member in task.all_eligible_claimants() and task.claimants.count() == 0:
            unclaimed_anytime.append((task, task_button_text(task)))

    template = loader.get_template('tasks/check_in_content.html')
    context = Context({
        'working_today'     : working_today,
        'claimed_today'     : claimed_today,
        'unclaimed_today'   : unclaimed_today,
        'unclaimed_anytime' : unclaimed_anytime,
        'member_card_str'   : member_card_str,
    })
    return template.render(context)


@kiosk_visitevent_contentprovider
def visitevent_departure_content(member, member_card_str, visit_event_type):

    # Short out if this isn't the event type this contentprovider handles.
    if visit_event_type != VisitEvent.EVT_DEPARTURE: return ""

    working_today = []      # Tasks the member is already working.

    # Find member's claimed tasks for today:
    for claim in member.claim_set.filter(
      status__in=[Claim.STAT_CURRENT,Claim.STAT_WORKING],
      claimed_task__scheduled_date=date.today()):
        if claim.status == Claim.STAT_WORKING:
            working_today.append((claim.claimed_task, task_button_text(claim)))

    template = loader.get_template('tasks/kiosk_check_out_content.html')
    context = Context({
        'working_today'     : working_today,
        'member_card_str'   : member_card_str,
    })
    return template.render(context)


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

        # TODO: There's some risk that user will end up here via browser history. Catch unique violoation exception?
        Claim.objects.create(
            claimed_task=task,
            claiming_member=nag.who,
            claimed_start_time=task.work_start_time,
            claimed_duration=timedelta(hours=t.hour, minutes=t.minute, seconds=t.second),
            status=Claim.STAT_CURRENT
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
            Claim.objects.create(
                claimed_task=t,
                claiming_member=nag.who,
                claimed_start_time=t.work_start_time,
                claimed_duration=t.max_work,
                status=Claim.STAT_CURRENT,
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

    if worker.calendar_token is None or len(worker.calendar_token) == 0:
        # I'm arbitrarily choosing md5str, below, but the fact that it came from md5 doesn't matter.
        _, md5str = Member.generate_auth_token_str(
            lambda t: Worker.objects.filter(calendar_token=t).count() == 0  # uniqueness test
        )
        worker.calendar_token = md5str
        worker.save()

    # Return page with a link to the calendar:
    return render(request, 'tasks/offers_done.html', {"worker": worker})


def cal_task_details(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    return render(request, "tasks/cal_task_details.html", {'task': task, 'notes':task.notes.all()})


def kiosk_task_details(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    return render(request, "tasks/kiosk_task_details.html", {'task': task, 'notes':task.notes.all()})


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = KIOSK = = = =

def _get_task_and_member(task_pk, member_card_str):

    logger = logging.getLogger("tasks")
    try:
        task = Task.objects.get(pk=task_pk)
    except Task.DOES_NOT_EXIST:
        msg = "Info provided doesn't correspond to a task."
        logger.error(msg)
        return None, None, JsonResponse({"error": msg})

    if task.work_start_time is None or task.work_duration is None:
        msg = "Expected a task with a specific time window."
        logger.error(msg)
        return None, None, JsonResponse({"error": msg})

    member = Member.get_by_card_str(member_card_str)
    if member is None:
        # This might legitimately occur if an invalidated card is presented at the kiosk.
        msg = "Info provided doesn't correspond to a member."
        logger.warning(msg)
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
        status=Claim.STAT_WORKING)
    return JsonResponse({"success": "A new claim was created and set to WORKING status."})


def record_work(request, task_pk, member_card_str):

    task, member, response = _get_task_and_member(task_pk, member_card_str)
    if response is not None: return response

    logger = logging.getLogger("tasks")

    if member not in task.claimants.all():
        msg = "You are not working on this task."
        logger.error(msg)
        return JsonResponse({"error": msg})

    claim = Claim.objects.get(claimed_task=task, claiming_member=member)
    if claim.status != Claim.STAT_WORKING:
        msg = "You are not working on this task."
        logger.error(msg)
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


def _add_event(cal, task, request):
    dtstart = datetime.combine(task.scheduled_date, task.work_start_time)
    relpath = reverse('task:cal-task-details', args=[task.pk])
    event = Event()
    event.add('uid',         task.pk)
    event.add('url',         request.build_absolute_uri(relpath))
    event.add('summary',     task.short_desc)
    event.add('description', task.instructions.replace("\r\n", " "))
    event.add('dtstart',     dtstart)
    event.add('dtend',       dtstart + task.work_duration)
    event.add('dtstamp',     datetime.now())
    cal.add_component(event)


def _ical_response(cal):
    ics = cal.to_ical()
    response = HttpResponse(ics, content_type='text/calendar')
    # TODO: No cache header?
    # TODO: Add filename?
    return response


def _gen_tasks_for(member):
    for task in member.tasks_claimed.all():
        if task.scheduled_date is None or task.work_start_time is None or task.work_duration is None:
            continue
        yield task


def _gen_all_tasks():
    for task in Task.objects.all():
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
    for task in _gen_tasks_for(member):
        _add_event(cal, task, request)
        #TODO: Add ALARM
    return _ical_response(cal)


def xerocraft_calendar(request):
    cal = _new_calendar("All Xerocraft Tasks")
    for task in _gen_all_tasks():
        _add_event(cal, task, request)
        # Intentionally lacks ALARM
    return _ical_response(cal)


def xerocraft_calendar_staffed(request):
    cal = _new_calendar("Xerocraft Staffed Tasks")
    for task in _gen_all_tasks():
        if task.is_fully_claimed():
            _add_event(cal, task, request)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def xerocraft_calendar_unstaffed(request):
    cal = _new_calendar("Xerocraft Unstaffed Tasks")
    for task in _gen_all_tasks():
        if not task.is_fully_claimed():
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

