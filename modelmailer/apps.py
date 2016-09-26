
# Standard

# Third Party
from django.apps import AppConfig

# Local
from abutils.utils import generic_autodiscover

__author__ = 'Adrian'


class ModelMailerAppConfig(AppConfig):
    name = 'modelmailer'
    verbose_name = 'Model Mailer'

    def ready(self):
        generic_autodiscover('mailviews')
