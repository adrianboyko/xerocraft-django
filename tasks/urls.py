from django.conf.urls import url

from . import views

urlpatterns = [

    # Part of the nag (aka "nudge") system:
    url(r'^offer-task/(?P<task_pk>[0-9]+)_(?P<auth_token>[-_a-zA-Z0-9]{32})/$', views.offer_task, name='offer-task'),

]
