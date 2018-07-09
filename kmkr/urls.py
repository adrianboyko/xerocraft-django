from django.conf.urls import url, include
from . import views

app_name = "kmkr"  # This is the app namespace not the app name.

urlpatterns = [

    url(r'^now-playing/$',
        views.now_playing,
        name='now-playing'),

    url(r'^now-playing-fbapp/$',
        views.now_playing_fbapp,
        name='now-playing-fbapp'),

    url(r'^now-playing-fbapp-privacy-policy/$',
        views.now_playing_fbapp_privacy_policy,
        name='now-playing-fbapp-privacy-policy'),

]
