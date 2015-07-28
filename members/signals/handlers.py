__author__ = 'Adrian'

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from members.models import Member, Tag, Tagging

@receiver(post_save, sender=User)
def create_default_member(sender, **kwargs):
    if kwargs.get('created', True):
        m,_ = Member.objects.get_or_create(auth_user=kwargs.get('instance'))

        try:
            t = Tag.objects.get(name="Member")
        except ObjectDoesNotExist:
            t = Tag.objects.create(name="Member",meaning="All members have this tag.")

        Tagging.objects.create(tagged_member=m, tag=t)

        m.save()


