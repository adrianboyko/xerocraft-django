
from django.urls import reverse


def get_url_str(obj):
    app = obj._meta.app_label
    mod = obj._meta.model_name
    url_name = 'admin:{}_{}_change'.format(app, mod)
    url_str = reverse(url_name, args=[obj.id])
    return url_str
