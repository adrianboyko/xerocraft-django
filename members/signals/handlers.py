from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User, user_logged_in
from django.core.exceptions import ObjectDoesNotExist
from members.models import Member, Tag, Tagging, PaidMembership, MemberLogin
import logging

__author__ = 'Adrian'

@receiver(post_save, sender=User)
def create_default_member(sender, **kwargs):
    if kwargs.get('created', True):

        m,_ = Member.objects.get_or_create(auth_user=kwargs.get('instance'))

        try:
            t = Tag.objects.get(name="Member")
        except ObjectDoesNotExist:
            t = Tag.objects.create(name="Member", meaning="All members have this tag.")

        Tagging.objects.create(tagged_member=m, tag=t)


@receiver(post_save, sender=Tagging)
def email_for_saved_tagging(sender, **kwargs):
    if kwargs.get('created', True):
        #TODO: Send SIGNED email to tagged_member informing them of addition, along with all other current tags.
        #TODO: Send email to authorizing_member informing them that this tagging was authorized in their name.
        #TODO: Send email to other members with the same can_tag privilege informing them.
        pass


@receiver(pre_save, sender=PaidMembership)
def link_paidmembership_to_member(sender, **kwargs):
    if kwargs.get('created', True):
        pm = kwargs.get('instance')
        if not pm.protected:
            pm.link_to_member()


def get_ip_address(request):
    """ Get client machine's IP address from request """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def note_login(sender, user, request, **kwargs):
    ip = get_ip_address(request)
    logger = logging.getLogger("members")
    logger.info("Login: %s at %s" % (user, ip))
    MemberLogin.objects.create(member=user.member, ip=ip)