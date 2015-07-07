from django.apps import AppConfig

class VolunteerAppConfig(AppConfig):
    name = 'tasks'
    verbose_name = 'Tasks and Workers'

    def ready(self):
        import tasks.signals.handlers #noqa