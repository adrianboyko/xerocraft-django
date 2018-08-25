# Standard
from datetime import timedelta
import logging

# Third Party
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

# Local
from members.models import Member, Tag, Tagging, MemberLogin, GroupMembership, Membership, VisitEvent
import members.notifications as notifications
from abutils.utils import get_ip_address

__author__ = 'Adrian'

logger = logging.getLogger("members")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# USER
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@receiver(post_save, sender=User)
def create_default_member(sender, **kwargs):
    """Whenever a User is created, create a corresponding Member and give it a Member tag."""
    if kwargs.get('created', True):

        m,_ = Member.objects.get_or_create(auth_user=kwargs.get('instance'))

        try:
            t = Tag.objects.get(name="Member")
        except ObjectDoesNotExist:
            t = Tag.objects.create(name="Member", meaning="All members have this tag.")

        Tagging.objects.create(member=m, tag=t, is_tagged=True, can_tag=False)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TAGGING
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# NOTE: DO NOT attempt to automatically manage group memberships here.


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# MEMBERSHIP
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# TODO: Attempt to auto-link based on name/email in sale. Only for WePay, 2Checkout, Square?
@receiver(pre_save, sender=Membership)
def link_membership_to_member(sender, **kwargs):
    if kwargs.get('created', True):
        mship = kwargs.get('instance')
        if not mship.protected:
            mship.link_to_member()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# LOGIN (No longer of interest)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# @receiver(user_logged_in)
# def note_login(sender, user, request, **kwargs):  # https://code.djangoproject.com/ticket/22111
#     try:
#         ip = get_ip_address(request)
#         if ip is None:
#             # IP is none when connecting from Client in tests.
#             # TODO: Assert that this is a dev machine?
#             return
#         logger.info("Login: %s at %s" % (user, ip))
#         MemberLogin.objects.create(member=user.member, ip=ip)
#
#         # TODO: Shouldn't have a hard-coded userid here. Make configurable, perhaps with tags.
#         recipient = Member.objects.get(auth_user__username='adrianb')
#         if recipient.auth_user != user:
#             message = "{}\n{}".format(user.username, ip)
#             notifications.notify(recipient, "Log-In", message)
#
#     except Exception as e:
#         # Failures here should not prevent the login from completing normally.
#         try:
#             logger.error("Problem noting login of %s from %s: %s", str(user), str(ip), str(e))
#         except Exception as e2:
#             logger.error("Problem noting login exception: %s", str(e2))


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# GROUP MEMBERSHIP
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@receiver(post_save, sender=GroupMembership)
def group_membership_post_save(sender, **kwargs):
    """Create the initial memberships based on the CURRENT taggings."""
    # Any further changes should be made through Admin.

    gm = kwargs.get('instance')
    if gm.membership_set.count() == 0:
        for taggee in gm.group_tag.members.all():  # type Member
            Membership.objects.create(
                member=taggee,
                group=gm,
                start_date=gm.start_date,
                end_date=gm.end_date,
                membership_type=Membership.MT_GROUP
            )


