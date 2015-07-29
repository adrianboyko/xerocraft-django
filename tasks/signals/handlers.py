__author__ = 'Adrian'

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from members.models import Member, Tag, Tagging

@receiver(post_save, sender=Tagging)
def create_default_member(sender, **kwargs):
    if kwargs.get('created', True):
        pass
        """ TODO: Check to see if this new tagging makes the tagged_member eligible for a task
            they weren't previously eligible for. If so, email them with info.
        """