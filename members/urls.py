from django.conf.urls import url, include
from . import views
from .restapi import views as restviews
from rest_framework import routers

app_name = "members"  # This is the app namespace not the app name.

router = routers.DefaultRouter()
router.register(r'members', restviews.MemberViewSet)
router.register(r'memberships', restviews.MembershipViewSet)
router.register(r'discovery-methods', restviews.DiscoveryMethodViewSet)
router.register(r'gift-card-refs', restviews.MembershipGiftCardReferenceViewSet)
router.register(r'wifi-mac-detected', restviews.WifiMacDetectedViewSet)
router.register(r'visit-events', restviews.VisitEventViewSet)

urlpatterns = [

    # For reception desk kiosk (check-in, sign-up, etc):

    url(r'^reception/$',
        views.reception_kiosk_spa,
        name="reception-kiosk"),

    # TODO: Verify that this URL is no longer used and delete it. Reception now uses REST API.
    url(r'^reception/matching-accts/(?P<flexid>[-a-zA-Z0-9_@+.]{1,32})/$',
        views.reception_kiosk_matching_accts,
        name="reception-kiosk-matching-accts"),

    url(r'^reception/checked-in-accts/$',
        views.reception_kiosk_checked_in_accts,
        name="reception-kiosk-checked-in-accts"),

    # TODO: Verify that this URL is no longer used and delete it. Reception now uses REST API.
    url(r'^reception/log-visit-event/(?P<member_pk>[0-9]*)_(?P<event_type>[APD])_(?P<reason>[A-Z]{3})/$',
        views.reception_kiosk_log_visit_event,
        name="reception-kiosk-log-visit-event"),

    url(r'^reception/add-discovery-method/$',
        views.reception_kiosk_add_discovery_method,
        name="reception-kiosk-add-discovery-method"),

    url(r'^reception/set-is-adult/$',
        views.reception_kiosk_set_is_adult,
        name="reception-kiosk-set-is-adult"),

    url(r'^reception/email-mship-buy-options/$',
        views.reception_kiosk_email_mship_buy_options,
        name="reception-kiosk-email-mship-buy-options"),

    # For desktop:
    # TODO: QR coded membership cards are no longer used.
    # TODO: Delete create-card and create-card-download.
    url(r'^create-card/$', views.create_card, name='create-card'),
    url(r'^create-card-download/$', views.create_card_download, name='create-card-download'),
    url(r'^desktop/member-tags/$', views.member_tags, name='desktop-member-tags'),
    url(r'^desktop/member-tags/(?P<member_pk>[0-9]+)(?P<op>[+-])(?P<tag_pk>[0-9]+)/$', views.member_tags, name='desktop-member-tags'),
    url(r'^desktop/member-count-vs-date/$', views.desktop_member_count_vs_date, name='desktop-member-count-vs-date'),
    url(r'^desktop/earned-membership-revenue/$', views.desktop_earned_membership_revenue, name='earned-membership-revenue'),

    # For mobile apps:
    # TODO: Mobile app is not currently used.
    # TODO: Verify that these URLs are not used elsewhere, then delete them.
    # TODO: Revise mobile app to use the REST API instead.
    url(r'^api/member-details/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<staff_card_str>[-_a-zA-Z0-9]{32})/$', views.api_member_details, name="api-member-details"),
    url(r'^api/member-details-pub/(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.api_member_details_pub, name="api-member-details-pub"),
    url(r'^api/visit-event/(?P<member_card_str>[-_a-zA-Z0-9]{32})_(?P<event_type>[APD])/$', views.api_log_visit_event, name="api-visit-event"),

    # DJANGO REST FRAMEWORK API (AKA "XisApi")
    url(r'^api/', include(router.urls)),
    url(r'^api-authenticate/', views.api_authenticate, name='api-authenticate'),

    # OTHER
    url(r'^csv/monthly-accrued-membership/$', views.csv_monthly_accrued_membership, name='csv-monthly-accrued-membership'),
    url(r'^csv/monthly-accrued-membership-download/$', views.csv_monthly_accrued_membership_download, name='csv-monthly-accrued-membership_download'),

    # RFID cards
    url(r'^rfid-entry-requested/(?P<rfid_cardnum>[0-9]{1,32})/$', views.rfid_entry_requested, name='rfid-entry-requested'),
    url(r'^rfid-entry-granted/(?P<rfid_cardnum>[0-9]{1,32})/$', views.rfid_entry_granted, name='rfid-entry-granted'),
    url(r'^rfid-entry-denied/(?P<rfid_cardnum>[0-9]{1,32})/$', views.rfid_entry_denied, name='rfid-entry-denied'),
]
