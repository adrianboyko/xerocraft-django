"""xerocraft URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

# Standard

# Third Party
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django_sabayon import urls as sabayon_urls

# Local
from xerops import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^test/$', views.test),
    url(r'^login/$', views.login),
    url(r'^accounting-menu/$', views.accounting_menu),
    url(r'^membership-status/(?P<provider>[-_.a-zA-Z0-9]+)/(?P<id>[-@+._a-zA-Z0-9]+)/$', views.api_get_membership_info),
    url(r'^scrape-xerocraft-org-checkins/$', views.scrape_xerocraft_org_checkins, name="scrape-xerocraft-org-checkins"),
    url(r'^paypal-webhook', views.paypal_webhook, name="paypal-webhook"),
    url(r'^credits/', views.credits, name="credits"),

    url(r'^logout/$', views.logout),
    url(r'^admin/login/', views.login),  # This shadows admin's login. REVIEW: Any downside?
    url(r'^admin/logout/', views.logout),  # This shadows admin's logout. REVIEW: Any downside?
    url(r'^admin/', include(admin.site.urls)),
    url(r'^members/', include('members.urls', namespace="memb")),
    url(r'^books/', include('books.urls', namespace="book")),
    url(r'^tasks/', include('tasks.urls', namespace="task")),
    url(r'^inventory/', include('inventory.urls', namespace="inv")),
    #url('', include('social.apps.django_app.urls', namespace='social')),

    # DJANGO REST FRAMEWORK API
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^helpdesk/', include('helpdesk.urls')),

    # The following is for auto-renewal of "letsencrypt" SSL certs
    url(r'^', include(sabayon_urls)),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
