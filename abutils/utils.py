# Standard
import uuid
import socket
import sys
from imp import find_module  # TODO: imp is deprecated
from importlib import import_module

# Third Party
from django.db.models import Model
from django.http import HttpRequest
from django.conf import settings


# Local


def generate_hex_string(length, uniqueness_check=None):
    assert(length <= 32)
    result = str(uuid.uuid4()).replace('-', '')[:length]
    if uniqueness_check is None or uniqueness_check(result):
        return result
    else:
        # Collision detected, so try again.
        return generate_hex_string(length, uniqueness_check)


def generate_ctrlid(model: Model) -> str:
    """Generate a unique ctrlid for the given model."""
    # TODO: Move this to ETL App if that refactorization is pursued.
    def is_unique(ctrlid: str) -> bool:
        if not hasattr(model, "ctrlid"):
            # This is necessary to support initialization of new blank databases.
            return True
        else:
            return model.objects.filter(ctrlid=ctrlid).count() == 0
    return "GEN:" + generate_hex_string(8, is_unique)


def get_ip_address(request: HttpRequest) -> str:
    """ Get client machine's IP address from request """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def request_is_from_host(request: HttpRequest, hostname: str) -> bool:
    req_ip = get_ip_address(request)
    host_ip = socket.gethostbyname(hostname)
    return req_ip == host_ip


# From https://djangosnippets.org/snippets/2404
def generic_autodiscover(module_name):
    """
    Dynamically autodiscover a particular module_name in a django project's
    INSTALLED_APPS directories, a-la django admin's autodiscover() method.

    Usage:
        generic_autodiscover('commands') <-- find all commands.py and load 'em
    """
    for app in settings.INSTALLED_APPS:
        try:
            import_module(app)
            app_path = sys.modules[app].__path__
        except AttributeError:
            continue
        try:
            find_module(module_name, app_path)
        except ImportError:
            continue
        import_module('%s.%s' % (app, module_name))
        app_path = sys.modules['%s.%s' % (app, module_name)]