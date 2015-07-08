from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^request-permit/$', views.request_parking_permit, name='request-permit'),
    url(r'^create-permit/$', views.create_parking_permit, name='create-permit'),
    url(r'^get-permit/(?P<pk>[0-9]+)/$', views.get_parking_permit, name='get-permit'),
    url(r'^rewnew-permits/$', views.renew_parking_permits, name='renew-permits'),
    url(r'^get-permit-scans/(?P<pk>[0-9]+)/$', views.get_parking_permit_scans, name='get-permit-scans'),
    url(r'^note-permit-scan/(?P<permit_pk>[0-9]+)_(?P<loc_name>[0-9]+)/$', views.note_parking_permit_scan, name='note-permit-scan'),
    url(r'^scan-instructions/$', views.parking_permit_scan_instructions, name='scan-instructions'),
    url(r'^get-location-qrs/(?P<start_pk>[0-9]+)/$', views.get_location_qrs, name='get-location-qrs'),
]
