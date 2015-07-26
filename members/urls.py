from django.conf.urls import url

from . import views

urlpatterns = [

    # For logged-in people:
    url(r'^create-card/$', views.create_membership_card, name='create-card'),

    # For people at kiosk:
    url(r'^kiosk/waiting/$', views.kiosk_waiting),
    url(r'^kiosk/member-details/(?P<membership_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_member_details),

    # For software:
    url(r'^tags/(?P<member_id>[0-9]+)/$', views.tags_for_member_pk),
    url(r'^read-card/(?P<membership_card_str>[-_a-zA-Z0-9]{32})/$', views.read_membership_card),

]

