from django.apps import AppConfig


class KmkrAppConfig(AppConfig):
    name = 'kmkr'

    def ready(self):
        import kmkr.signals.handlers