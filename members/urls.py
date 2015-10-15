from django.conf.urls import url

from . import views

urlpatterns = [

    # For logged-in members:
    url(r'^create-card/$', views.create_membership_card, name='create-card'),

    # For kiosk:
    url(r'^kiosk/waiting/$', views.kiosk_waiting),
    url(r'^kiosk/main-menu/(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_main_menu, name="kiosk-main-menu"),
    url(r'^kiosk/staff-menu/(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_staff_menu, name="kiosk-staff-menu"),
    url(r'^kiosk/identify-subject/(?P<staff_card_str>[-_a-zA-Z0-9]{32})_(?P<next_url>[-a-z]+)/$', views.kiosk_identify_subject, name="kiosk-identify-subject"),
    url(r'^kiosk/check-in-member/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<event_type>[APD])/$', views.Kiosk_LogVisitEvent.as_view(), name="kiosk-check-in-member"),
    url(r'^kiosk/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_member_details, name="kiosk-member-details"),
    url(r'^kiosk/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/(?P<tag_pk>[0-9]+)/', views.kiosk_add_tag),

    # For mobile apps:
    url(r'^api/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/$', views.api_member_details, name="api-member-details"),
    url(r'^api/member-details-pub/(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.api_member_details_pub, name="api-member-details-pub"),
    url(r'^api/visit-event/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<event_type>[APD])/$', views.api_log_visit_event, name="api-visit-event"),

]

