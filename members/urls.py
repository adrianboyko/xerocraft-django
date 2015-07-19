from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^tags/(?P<member_id>[0-9]+)/$', views.tags_for_member_pk),
    url(r'^read-card/(?P<membership_card_str>[-_a-zA-Z0-9]{32})/$', views.read_membership_card),
    url(r'^create-card/$', views.create_membership_card),
]

