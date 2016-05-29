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

    url(r'^net-income-vs-date-chart/$', views.net_income_vs_date_chart, name='net-income-vs-date-chart'),
    url(r'^net-income-vs-date-chart/2/$', views.net_income_vs_date_chart_2, name='net-income-vs-date-chart-2'),

    # DJANGO REST FRAMEWORK API
    url(r'^', include(router.urls)),
]

