from django.conf.urls import url, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'sales', views.SaleViewSet)
router.register(r'sale-notes', views.SaleNoteViewSet)
router.register(r'monetary-donations', views.MonetaryDonationViewSet)
router.register(r'other-items', views.OtherItemViewSet)
router.register(r'other-item-types', views.OtherItemTypeViewSet)

urlpatterns = [

    url(r'^cumulative-vs-date-chart/$', views.cumulative_vs_date_chart, name='cumulative-vs-date-chart'),
    url(r'^cumulative-vs-date-chart/2/$', views.cumulative_vs_date_chart, name='cumulative-vs-date-chart'),

    # DJANGO REST FRAMEWORK API
    url(r'^', include(router.urls)),
]

