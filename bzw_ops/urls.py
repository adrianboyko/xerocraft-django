# Standard

# Third Party
from django.conf.urls import include, url
from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

# Local
from bzw_ops import views
import bzw_ops.restapi.views as restviews
import xis.views

router = routers.DefaultRouter()
router.register(r'time_blocks', restviews.TimeBlockViewSet)
router.register(r'time_block_types', restviews.TimeBlockTypeViewSet)

urlpatterns = [
    url(r'^$', views.index),
    url(r'^test/$', views.test),
    url(r'^login/$', views.login),
    url(r'^logout/$', views.logout),
    url(r'^accounting-menu/$', views.accounting_menu),
    url(r'^membership-status/(?P<provider>[-_.a-zA-Z0-9]+)/(?P<id>[-@+._a-zA-Z0-9]+)/$', views.api_get_membership_info),
    url(r'^scrape-xerocraft-org-checkins/$', xis.views.scrape_xerocraft_org_checkins, name="scrape-xerocraft-org-checkins"),
    url(r'^paypal-webhook', views.paypal_webhook, name="paypal-webhook"),
    url(r'^credits/', views.credits, name="credits"),

    url(r'^admin/login/', views.login),  # This shadows admin's login. REVIEW: Any downside?
    url(r'^admin/logout/', views.logout),  # This shadows admin's logout. REVIEW: Any downside?
    url(r'^admin/', admin.site.urls),
    url(r'^members/', include('members.urls', namespace="memb")),
    url(r'^books/', include('books.urls', namespace="book")),
    url(r'^soda/', include('soda.urls', namespace="soda")),
    url(r'^tasks/', include('tasks.urls', namespace="task")),
    url(r'^inventory/', include('inventory.urls', namespace="inv")),
    url(r'^xis/', include('xis.urls', namespace="xis")),
    #url('', include('social.apps.django_app.urls', namespace='social')),

    # DJANGO REST FRAMEWORK API
    url(r'^ops/api/', include(router.urls)),
    url(r'^ops/log-message/$', views.log_message),

    url(r'^helpdesk/', include('helpdesk.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]