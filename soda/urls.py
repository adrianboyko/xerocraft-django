# Standard

# Third Party
from django.conf.urls import url, include
from rest_framework import routers

# Local
import soda.restapi.views as restviews

app_name = "soda"  # This is the app namespace not the app name.

router = routers.DefaultRouter()
router.register(r'vendlog', restviews.VendLogViewSet)

urlpatterns = [

    # DJANGO REST FRAMEWORK API
    url(r'^api/', include(router.urls)),
    #url(r'^api/schema/', views.schema_view),

]
