# Standard

# Third Party
from django.conf.urls import url, include
from rest_framework import routers

# Local
import tasks.views as views
import tasks.restapi.views as restviews

app_name = "tasks"  # This is the app namespace not the app name.

router = routers.DefaultRouter()
router.register(r'tasks', restviews.TaskViewSet)
router.register(r'classes', restviews.ClassViewSet)
router.register(r'classxpersons', restviews.ClassXPesronViewSet)
router.register(r'claims', restviews.ClaimViewSet)
router.register(r'plays', restviews.PlayViewSet)
router.register(r'workers', restviews.WorkerViewSet)
router.register(r'works', restviews.WorkViewSet)
router.register(r'worknotes', restviews.WorkNoteViewSet)

urlpatterns = [

    # General
    url(r'^kiosk-task-details/(?P<task_pk>[0-9]+)/$', views.kiosk_task_details, name='kiosk-task-details'),
    url(r'^time-acct-statement/(?P<range>(all)|(recent))/$', views.time_acct_statement, name='time-acct-statement'),

    # API
    url(r'^will-work-now/(?P<task_pk>[0-9]+)_(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.will_work_now, name='will-work-now'),
    url(r'^record_work/(?P<task_pk>[0-9]+)_(?P<member_card_str>[-_a-zA-Z0-9]{32})/$', views.record_work, name='record_work'),

    # Nag related views:
    url(r'^offer-task/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$',
        views.offer_task, name='offer-task'),
    url(r'^offer-more-tasks/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$',
        views.offer_more_tasks, name='offer-more-tasks'),
    url(r'^offers-done/(?P<auth_token>[-_a-zA-Z0-9]{32})/$',
        views.offers_done, name='offers-done'),
    url(r'^note_task_done/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$',
        views.note_task_done, name='note-task-done'),

    # Verify auto claims:
    url(r'^verify-claim/(?P<task_pk>[0-9]+)_(?P<claim_pk>[0-9]+)_(?P<will_do>[YN])_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.verify_claim, name='verify-claim'),

    # Experimenting with SPA/React versions of nag and verify
    url(r'^offer-task-spa/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_task_spa, name='offer-task-spa'),
    # url(r'^verify-claim-spa/$', views.verify_claim_spa, name='verify-claim-spa'),

    # Calendar for a given worker
    url(r'^member-calendar/(?P<token>[-_a-zA-Z0-9]{32})/$', views.member_calendar, name='member-calendar'),

    url(r'^resource-calendar/$', views.resource_calendar, name='resource-calendar'),

    # Operations calendar, i.e. various staffing tasks.
    url(r'^ops-calendar/$', views.ops_calendar, name='ops-calendar'),
    url(r'^ops-calendar/staffed/$', views.ops_calendar_staffed, name='ops-calendar-staffed'),
    url(r'^ops-calendar/provisional/$', views.ops_calendar_provisional, name='ops-calendar-provisional'),
    url(r'^ops-calendar/unstaffed/$', views.ops_calendar_unstaffed, name='ops-calendar-unstaffed'),
    url(r'^ops-calendar-spa/$', views.ops_calendar_spa, name='ops-calendar-spa'),
    url(r'^ops-calendar-spa/(?P<year>[0-9]{4})-(?P<month>[01]?[0-9])/$', views.ops_calendar_spa, name='ops-calendar-spa-ymintiin'),

    url(r'^cal-task-details/(?P<task_pk>[0-9]+)/$', views.cal_task_details, name='cal-task-details'),

    # Temporary Work Trade Checkout
    url(r'^desktop-timesheet/$', views.desktop_timesheet, name='desktop-timesheet'),

    # DJANGO REST FRAMEWORK API
    url(r'^api/', include(router.urls)),
    #url(r'^api/schema/', views.schema_view),

]
