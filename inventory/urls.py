from django.conf.urls import url

from . import views

urlpatterns = [

    # For all members:
    url(r'^desktop/request-parking-permit/$', views.desktop_request_parking_permit, name='desktop-request-parking-permit'),
    url(r'^desktop/approve-parking-permit/$', views.desktop_approve_parking_permit, name='desktop-approve-parking-permit'),
    url(r'^desktop/verify-parking-permit/$', views.desktop_verify_parking_permit, name='desktop-verify-parking-permit'),
    url(r'^print-parking-permit/(?P<pk>[0-9]+)/$', views.print_parking_permit, name='print-parking-permit'),

    url(r'^list-my-permits/$', views.list_my_permits, name='list-my-permits'),
    url(r'^rewnew-permits/$', views.renew_parking_permits, name='renew-permits'),

    # For staff:
    url(r'^inventory-todos/$', views.inventory_todos, name='inventory-todos'),
    url(r'^get-location-qrs/(?P<start_pk>[0-9]+)/$', views.get_location_qrs, name='get-location-qrs'),

    # For apps:
    url(r'^get-permit-details/(?P<pk>[0-9]+)/$', views.get_parking_permit_details, name='get-permit-details'),
    url(r'^note-permit-scan/(?P<permit_pk>[0-9]+)_(?P<loc_pk>[0-9]+)/$', views.note_parking_permit_scan, name='note-permit-scan'),

]
