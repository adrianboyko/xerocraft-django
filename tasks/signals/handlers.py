# Standard
import logging
from datetime import date

# Third Party
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

# Local
from members.models import Member, Tagging, VisitEvent, Pushover
from tasks.models import Task, Worker, Claim
import members.notifications as notifications

__author__ = 'Adrian'

logger = logging.getLogger("tasks")


@receiver(post_save, sender=Tagging)
def act_on_new_tag(sender, **kwargs):
    if kwargs.get('created', True):
        pass
        """ TODO: Check to see if this new tagging makes the tagged_member eligible for a task
            they weren't previously eligible for. If so, email them with info.
        """


@receiver(post_save, sender=Member)
def create_default_worker(sender, **kwargs):
    if kwargs.get('created', True):
        w,_ = Worker.objects.get_or_create(member=kwargs.get('instance'))


@receiver(pre_save, sender=Claim)
def staffing_update_notification(sender, **kwargs):
    try:
        if kwargs.get('created', True):
            claim = kwargs.get('instance')  # type: Claim
            message = None
            if claim.status in [Claim.STAT_UNINTERESTED, Claim.STAT_ABANDONED, Claim.STAT_EXPIRED]:
                message = "{0} will NOT work '{1}' on {2:%a %m/%d}".format(
                    claim.claiming_member.friendly_name,
                    claim.claimed_task.short_desc,
                    claim.claimed_task.scheduled_date
                )
            if claim.status == Claim.STAT_CURRENT and claim.date_verified is not None:
                message = "{0} WILL work '{1}' on {2:%a %m/%d}".format(
                    claim.claiming_member.friendly_name,
                    claim.claimed_task.short_desc,
                    claim.claimed_task.scheduled_date
                )
            if message is not None:
                recipient = Member.objects.get(auth_user__username='adrianb')
                notifications.notify(recipient, "Staffing Update", message)

    except Exception as e:
        logger.error("Problem sending staffing update.")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# VISIT
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@receiver(post_save, sender=VisitEvent)
def maintenance_nag(sender, **kwargs):
    try:
        if kwargs.get('created', True):
            visit = kwargs.get('instance')  # type: VisitEvent

            # We're only interested in arrivals
            if visit.event_type != VisitEvent.EVT_ARRIVAL:
                return

            # Only act on a member's first visit of the day.
            num_visits_today = VisitEvent.objects.filter(
                who=visit.who,
                type=VisitEvent.EVT_ARRIVAL,
                when__gte=date.today(),
            ).count()
            if num_visits_today > 1:
                return

            # This gets tasks that are scheduled like maintenance tasks.
            # I.e. those that need to be done every X days, but can slide.
            tasks = Task.objects.filter(
                eligible_claimants=visit.who,
                scheduled_date=date.today(),
                status=Task.STAT_ACTIVE,
                should_nag=True,
                recurring_task_template__repeat_interval__isnull=False,
                recurring_task_template__missed_date_action=Task.MDA_SLIDE_SELF_AND_LATER,
            )

            if len(tasks)>0 and Pushover.getkey(visit.who) is None:
                logger.info(
                    "Wanted to notify %s of task(s) but Pushover key not available.",
                    visit.who.friendly_name
                )
                return

            for task in tasks:  # type: Task
                pass
                # TODO
                # message = "..."
                # notifications.notify(visit.who, task.short_desc, message)

    except Exception as e:
        # Makes sure that problems here do not prevent the visit event from being saved!
        logger.error("Problem in maintenance_nag: %s", str(e))

