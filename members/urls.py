from django.conf.urls import url

from . import views

urlpatterns = [

    # For logged-in members:
    url(r'^create-card/$', views.create_membership_card, name='create-card'),

    # For kiosk:
    url(r'^kiosk/waiting/$', views.kiosk_waiting),
    url(r'^kiosk/check-in-member/(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_check_in_member),
    url(r'^kiosk/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_member_details, name="kiosk-member-details"),
    url(r'^kiosk/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/(?P<tag_pk>[0-9]+)/', views.kiosk_add_tag),

    # For mobile apps:
    url(r'^tags/(?P<member_id>[0-9]+)/$', views.tags_for_member_pk),
    url(r'^read-card/(?P<membership_card_str>[-_a-zA-Z0-9]{32})/$', views.read_membership_card),

]

