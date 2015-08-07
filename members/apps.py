__author__ = 'Adrian'

from django.apps import AppConfig


class MembersAppConfig(AppConfig):
    name = 'members'
    verbose_name = 'Members'

    def ready(self):
        import members.signals.handlers