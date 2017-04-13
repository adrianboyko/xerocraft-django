
# Standard
from typing import Union
import sys

# Third-Party
from django.db.models.signals import m2m_changed, pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver

# Local
from ..models import (
    Person, PersonInClassTemplate,
    Resource, ResourceInClassTemplate,
    TimePattern,
)

__author__ = 'Adrian'


@receiver(post_save, sender=PersonInClassTemplate)
def post_personinclasstemplate_save(sender, **kwargs):
    instance = kwargs.get('instance')  # type: PersonInClassTemplate
    instance.note_personinclasstemplate_change()


@receiver(post_save, sender=ResourceInClassTemplate)
def post_resourceinclasstemplate_save(sender, **kwargs):
    instance = kwargs.get('instance')  # type: ResourceInClassTemplate
    instance.note_resourceinclasstemplate_change()


@receiver(post_save, sender=TimePattern)
def post_timepattern_save(sender, **kwargs):
    instance = kwargs.get('instance')  # type: TimePattern
    instance.note_timepattern_change()

