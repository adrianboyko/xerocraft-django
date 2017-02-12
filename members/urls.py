from django.conf.urls import url, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'members', views.MemberViewSet)
router.register(r'memberships', views.MembershipViewSet)
router.register(r'discovery-methods', views.DiscoveryMethodViewSet)
router.register(r'gift-card-refs', views.MembershipGiftCardReferenceViewSet)
router.register(r'wifi-mac-detected', views.WifiMacDetectedViewSet)

urlpatterns = [

    # For desktop:
    url(r'^create-card/$', views.create_card, name='create-card'),
    url(r'^create-card-download/$', views.create_card_download, name='create-card-download'),
    url(r'^desktop/member-tags/$', views.member_tags, name='desktop-member-tags'),
    url(r'^desktop/member-tags/(?P<member_pk>[0-9]+)(?P<op>[+-])(?P<tag_pk>[0-9]+)/$', views.member_tags, name='desktop-member-tags'),
    url(r'^desktop/member-count-vs-date/$', views.desktop_member_count_vs_date, name='desktop-member-count-vs-date'),
    url(r'^desktop/earned-membership-revenue/$', views.desktop_earned_membership_revenue, name='earned-membership-revenue'),

    # For generic kiosk (ABANDONED):
    url(r'^kiosk/waiting/$', views.kiosk_waiting),
    url(r'^kiosk/main-menu/(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_main_menu, name="kiosk-main-menu"),
    url(r'^kiosk/staff-menu/(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_staff_menu, name="kiosk-staff-menu"),
    url(r'^kiosk/identify-subject/(?P<staff_card_str>[-_a-zA-Z0-9]{32})_(?P<next_url>[-a-z]+)/$', views.kiosk_identify_subject, name="kiosk-identify-subject"),
    url(r'^kiosk/check-in-member/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<event_type>[APD])/$', views.Kiosk_LogVisitEvent.as_view(), name="kiosk-check-in-member"),
    url(r'^kiosk/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/$', views.kiosk_member_details, name="kiosk-member-details"),
    url(r'^kiosk/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/(?P<tag_pk>[0-9]+)/', views.kiosk_add_tag),

    # For reception kiosk (check-in, sign-up, etc):
    url(r'^reception/$', views.reception_kiosk_spa),

    # For mobile apps:
    url(r'^api/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/$', views.api_member_details, name="api-member-details"),
    url(r'^api/member-details-pub/(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.api_member_details_pub, name="api-member-details-pub"),
    url(r'^api/visit-event/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<event_type>[APD])/$', views.api_log_visit_event, name="api-visit-event"),

    # DJANGO REST FRAMEWORK API
    url(r'^api/', include(router.urls)),

    # OTHER
    url(r'^csv/monthly-accrued-membership/$', views.csv_monthly_accrued_membership, name='csv-monthly-accrued-membership'),
    url(r'^csv/monthly-accrued-membership-download/$', views.csv_monthly_accrued_membership_download, name='csv-monthly-accrued-membership_download'),

    # RFID cards
    url(r'^rfid-entry-requested/(?P<rfid_cardnum>[0-9]{1,32})/$', views.rfid_entry_requested, name='rfid-entry-requested'),
    url(r'^rfid-entry-granted/(?P<rfid_cardnum>[0-9]{1,32})/$', views.rfid_entry_granted, name='rfid-entry-granted'),
    url(r'^rfid-entry-denied/(?P<rfid_cardnum>[0-9]{1,32})/$', views.rfid_entry_denied, name='rfid-entry-denied'),
]
