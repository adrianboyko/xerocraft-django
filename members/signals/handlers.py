from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from members.models import Member, Tag, Tagging, PaidMembership

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
        kwargs.get('instance').link_to_member()
