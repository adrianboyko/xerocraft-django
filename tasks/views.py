from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse, Http404
from django.template import loader, Context
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from hashlib import md5
from datetime import date, datetime, timedelta

from tasks.models import Task, Nag, Claim, CalendarSettings
from members.models import Member, VisitEvent

from icalendar import Calendar, Event


# = = = = = = = = = = = = = = = = = = = = KIOSK VISIT EVENT CONTENT PROVIDERS

from members.views import kiosk_visitevent_contentprovider


def visitevent_arrival_content(member):

    claimed_today = []      # The member's claimed tasks for today
    unclaimed_today = []    # Other tasks scheduled for today that the member could claim
    unclaimed_anytime = []  # Other unscheduled tasks that the member could claim

    # Find member's claimed tasks for today:
    for claim in member.claim_set.filter(status=Claim.STAT_CURRENT, claimed_task__scheduled_date=date.today()):
        claimed_today.append(claim.claimed_task)

    # Find today's unclaimed tasks:
    for task in Task.objects.filter(status=Task.STAT_ACTIVE, scheduled_date=date.today()):
        if member in task.all_eligible_claimants() and task.claimants.count() == 0:
            unclaimed_today.append(task)

    # Find unclaimed tasks with no scheduled date:
    for task in Task.objects.filter(status=Task.STAT_ACTIVE, scheduled_date__isnull=True):
        if member in task.all_eligible_claimants() and task.claimants.count() == 0:
            unclaimed_anytime.append(task)

    template = loader.get_template('tasks/check_in_content.html')
    context = Context({
        'claimed_today'     : claimed_today,
        'unclaimed_today'   : unclaimed_today,
        'unclaimed_anytime' : unclaimed_anytime,
    })
    return template.render(context)


def visitevent_departure_content(member):
    return ""

@kiosk_visitevent_contentprovider
def visitevent_content(member, visit_event_type):
    if visit_event_type == VisitEvent.EVT_ARRIVAL:
        return visitevent_arrival_content(member)
    if visit_event_type == VisitEvent.EVT_DEPARTURE:
        return visitevent_departure_content(member)


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

    # Get the member's calendar settings, or create them if they don't exist:
    try:
        settings = CalendarSettings.objects.get(who=member)
    except CalendarSettings.DoesNotExist:
        # I'm arbitrarily choosing md5str, below, but the fact that it came from md5 doesn't matter.
        _, md5str = Member.generate_auth_token_str(
            lambda t: CalendarSettings.objects.filter(token=t).count() == 0  # uniqueness test
        )
        settings = CalendarSettings.objects.create(who=member, token=md5str)

    # Return page with a link to the calendar:
    return render(request, 'tasks/offers_done.html', {"member": member, "settings": settings})


def task_details(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    return render(request, "tasks/task_details.html", {'task': task})

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


def _add_event(cal, task):
    dtstart = datetime.combine(task.scheduled_date, task.work_start_time)
    event = Event()
    event.add('uid',         task.pk)
    event.add('url',         "http://xerocraft-django.herokuapp.com/tasks/task-details/%d/" % task.pk)  # TODO: Lookup instead of hard code?
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

    # See if token corresponds to a CalendarSettings token:
    try:
        cal_settings = CalendarSettings.objects.get(token=token)
        member = cal_settings.who
    except Nag.DoesNotExist:
        member = None

    # If token didn't correspond to nag, see if it's a member card string:
    if member is None:
        member = Member.get_by_card_str(token)

    if member is None:
        raise Http404("No such calendar")

    cal = _new_calendar("My Xerocraft Tasks")
    for task in _gen_tasks_for(member):
        _add_event(cal, task)
        #TODO: Add ALARM
    return _ical_response(cal)


def xerocraft_calendar(request):
    cal = _new_calendar("All Xerocraft Tasks")
    for task in _gen_all_tasks():
        _add_event(cal, task)
        # Intentionally lacks ALARM
    return _ical_response(cal)


def xerocraft_calendar_staffed(request):
    cal = _new_calendar("Xerocraft Staffed Tasks")
    for task in _gen_all_tasks():
        if task.is_fully_claimed():
            _add_event(cal, task)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def xerocraft_calendar_unstaffed(request):
    cal = _new_calendar("Xerocraft Unstaffed Tasks")
    for task in _gen_all_tasks():
        if not task.is_fully_claimed():
            _add_event(cal, task)
            # Intentionally lacks ALARM
    return _ical_response(cal)


def resource_calendar(request):
    cal = _new_calendar("Xerocraft Resource Usage")
    #for task in Task.objects.all():
    #    if task.scheduled_date is None or task.work_start_time is None or task.work_duration is None:
    #        continue
    #    _add_event(cal,task)
    #    # Intentionally lacks ALARM
    return _ical_response(cal)

