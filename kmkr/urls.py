from django.conf.urls import url, include
from . import views

app_name = "kmkr"  # This is the app namespace not the app name.

urlpatterns = [

    url(r'^now-playing/$',
        views.now_playing,
        name='now-playing'),
]
