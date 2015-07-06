from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^request-permit/$', views.request_parking_permit, name='request-permit'),
    url(r'^create-permit/$', views.create_parking_permit, name='create-permit'),
    url(r'^get-permit/(?P<pk>[0-9]+)/$', views.get_parking_permit, name='get-permit'),
    url(r'^rewnew-permits/$', views.renew_parking_permits, name='renew-permits'),
]
