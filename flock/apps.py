from django.apps import AppConfig


class FlockAppConfig(AppConfig):
    name = 'flock'
    isready = False

    def ready(self):
        if self.isready:
            return
        else:
            self.isready = True
            import flock.signals.handlers