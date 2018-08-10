from django.conf.urls import url, include
from . import views
from .restapi import views as restviews
from rest_framework import routers

app_name = "kmkr"  # This is the app namespace not the app name.

router = routers.DefaultRouter()
router.register(r'playlogentries', restviews.PlayLogEntryViewSet)
router.register(r'shows', restviews.ShowViewSet)
router.register(r'tracks', restviews.TrackViewSet)
router.register(r'show-instances', restviews.EpisodeViewSet)
router.register(r'manual-playlist-entries', restviews.EpisodeTrackViewSet)

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

    url(r'^dj-ops/$',
        views.dj_ops_spa,
        name='track-logger-spa'),

    url(r'^api/', include(router.urls)),

]
