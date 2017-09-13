from django.apps import AppConfig


class BezewyOpsAppConfig(AppConfig):
    name = 'bzw_ops'
    verbose_name = 'Bezewy Ops'

    def ready(self):
        import bzw_ops.signals.handlers