# Standard
from datetime import timedelta
import logging

# Third Party
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

# Local
from members.models import Member, VisitEvent
import members.notifications as notifications
from tasks.models import Worker, Task, Claim

__author__ = 'Adrian'

logger = logging.getLogger("bezewy-ops")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# VISIT
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@receiver(pre_save, sender=VisitEvent)  # Making this PRE-save because I want to get latest before save.
def note_checkin(sender, **kwargs):
    try:
        if kwargs.get('created', True):
            visit = kwargs.get('instance')

            # We're only interested in arrivals
            if visit.event_type != VisitEvent.EVT_ARRIVAL:
                return

            recipient = Worker.scheduled_receptionist()
            if recipient is None:
                return

            # RFID checkin systems may fire multiple times. Skip checkin if "too close" to the prev checkin time.
            try:
                recent_visit = VisitEvent.objects.filter(who=visit.who, event_type=VisitEvent.EVT_ARRIVAL).latest('when')
                delta = visit.when - recent_visit.when
            except VisitEvent.DoesNotExist:
                delta = timedelta.max
            if delta < timedelta(hours=1):
                return

            vname = "{} {}".format(visit.who.first_name, visit.who.last_name).strip()
            vname = "Anonymous" if len(vname) == "" else vname
            vstat = "Paid" if visit.who.is_currently_paid() else "Unpaid"

            message = "{}\n{}\n{}".format(visit.who.username, vname, vstat)
            notifications.notify(recipient, "Check-In", message)

    except Exception as e:
        # Makes sure that problems here do not prevent the visit event from being saved!
        logger.error("Problem in note_checkin: %s", str(e))

