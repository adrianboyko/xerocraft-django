from django.conf.urls import url

from . import views

urlpatterns = [

    # General
    url(r'^task-details/(?P<task_pk>[0-9]+)/$', views.task_details, name='task-details'),

    # Part of the nag (aka "nudge") system:
    url(r'^offer-task/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_task, name='offer-task'),
    url(r'^offer-more-tasks/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_more_tasks, name='offer-more-tasks'),
    url(r'^offers-done/(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offers_done, name='offers-done'),

    # Calendars
    url(r'^member-calendar/(?P<token>[-_a-zA-Z0-9]{32})/$', views.member_calendar, name='member-calendar'),
    url(r'^resource-calendar/$', views.resource_calendar, name='resource-calendar'),
    url(r'^xerocraft-calendar/$', views.xerocraft_calendar, name='xerocraft-calendar'),

]
