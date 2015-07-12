from django.conf.urls import url

from . import views

urlpatterns = [

    # For all members:
    url(r'^$', views.index, name='index'),
    url(r'^request-permit/$', views.request_parking_permit, name='request-permit'),
    url(r'^list-my-permits/$', views.list_my_permits, name='list-my-permits'),
    url(r'^get-permit/(?P<pk>[0-9]+)/$', views.get_parking_permit, name='get-permit'),
    url(r'^rewnew-permits/$', views.renew_parking_permits, name='renew-permits'),

    # For staff:
    url(r'^inventory-todos/$', views.inventory_todos, name='inventory-todos'),
    url(r'^get-location-qrs/(?P<start_pk>[0-9]+)/$', views.get_location_qrs, name='get-location-qrs'),

    # Internal:
    url(r'^create-permit/$', views.create_parking_permit, name='create-permit'),

    # For apps:
    url(r'^get-permit-scans/(?P<pk>[0-9]+)/$', views.get_parking_permit_scans, name='get-permit-scans'),
    url(r'^note-permit-scan/(?P<permit_pk>[0-9]+)_(?P<loc_pk>[0-9]+)/$', views.note_parking_permit_scan, name='note-permit-scan'),

]
