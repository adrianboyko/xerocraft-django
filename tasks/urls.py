from django.conf.urls import url

from . import views

urlpatterns = [

    # Part of the nag (aka "nudge") system:
    url(r'^offer-task/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_task, name='offer-task'),
    url(r'^offer-more-tasks/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_more_tasks, name='offer-more-tasks'),
    url(r'^offer-adjacent-tasks/(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_adjacent_tasks, name='offer-adjacent-tasks'),
    url(r'^offers-done/(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offers_done, name='offers-done'),


    # Calendars
    url(r'^all-xerocraft-tasks.ics$', views.AllTasksFeed(), name='all-xerocraft-tasks'),
    url(r'^my-xerocraft-tasks.ics$', views.MyTasksFeed(), name='my-xerocraft-tasks'),

]
