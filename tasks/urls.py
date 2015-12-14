from django.conf.urls import url

from . import views

urlpatterns = [

    # General
    url(r'^kiosk-task-details/(?P<task_pk>[0-9]+)/$', views.kiosk_task_details, name='kiosk-task-details'),

    # API
    url(r'^will-work-now/(?P<task_pk>[0-9]+)_(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.will_work_now, name='will-work-now'),
    url(r'^record_work/(?P<task_pk>[0-9]+)_(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.record_work, name='record_work'),

    # Part of the nag (aka "nudge") system:
    url(r'^offer-task/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_task, name='offer-task'),
    url(r'^offer-more-tasks/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_more_tasks, name='offer-more-tasks'),
    url(r'^offers-done/(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offers_done, name='offers-done'),

    # Calendars
    url(r'^member-calendar/(?P<token>[-_a-zA-Z0-9]{32})/$', views.member_calendar, name='member-calendar'),
    url(r'^resource-calendar/$', views.resource_calendar, name='resource-calendar'),
    url(r'^xerocraft-calendar/$', views.xerocraft_calendar, name='xerocraft-calendar'),
    url(r'^xerocraft-calendar/staffed/$', views.xerocraft_calendar_staffed, name='xerocraft-calendar-staffed'),
    url(r'^xerocraft-calendar/unstaffed/$', views.xerocraft_calendar_unstaffed, name='xerocraft-calendar-unstaffed'),
    url(r'^cal-task-details/(?P<task_pk>[0-9]+)/$', views.cal_task_details, name='cal-task-details'),

    # Temporary Work Trade Checkout
    url(r'^desktop-timesheet/$', views.desktop_timesheet, name='desktop-timesheet'),
    url(r'^desktop-timesheet-verify/$', views.desktop_timesheet_verify, name='desktop-timesheet-verify'),

]
