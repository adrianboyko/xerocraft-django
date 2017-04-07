from django.apps import AppConfig


class BezewyOpsAppConfig(AppConfig):
    name = 'xerops'
    verbose_name = 'Bezewy Ops'

    def ready(self):
        import xerops.signals.handlers