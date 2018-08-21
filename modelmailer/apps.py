
# Standard

# Third Party
from django.apps import AppConfig

# Local

__author__ = 'Adrian'


class ModelMailerAppConfig(AppConfig):
    name = 'modelmailer'
    verbose_name = 'Model Mailer'

    def ready(self):
        from django.utils.module_loading import autodiscover_modules
        autodiscover_modules('mailviews')