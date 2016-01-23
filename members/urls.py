from django.conf.urls import url, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'paidmemberships', views.PaidMembershipViewSet)

urlpatterns = [

    # For desktop:
    url(r'^create-card/$', views.create_card, name='create-card'),
    url(r'^create-card-download/$', views.create_card_download, name='create-card-download'),
    url(r'^desktop/member-tags/$', views.member_tags, name='desktop-member-tags'),
    url(r'^desktop/member-tags/(?P<member_pk>[0-9]+)(?P<op>[+-])(?P<tag_pk>[0-9]+)/$', views.member_tags, name='desktop-member-tags'),
    url(r'^desktop/member-count-vs-date/$', views.desktop_member_count_vs_date, name='desktop-member-count-vs-date'),

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

    # DJANGO REST FRAMEWORK API
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))

]

