# Standard
import logging

# Third Party
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

# Local
from members.models import Member, Tag, Tagging
from tasks.models import Worker, Claim
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
