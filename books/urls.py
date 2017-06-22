from django.conf.urls import url, include
from . import views
from rest_framework import routers

app_name = "books"  # This is the app namespace not the app name.

router = routers.DefaultRouter()
router.register(r'sales', views.SaleViewSet)
router.register(r'sale-notes', views.SaleNoteViewSet)
router.register(r'monetary-donations', views.MonetaryDonationViewSet)
router.register(r'other-items', views.OtherItemViewSet)
router.register(r'other-item-types', views.OtherItemTypeViewSet)

urlpatterns = [

    # url(r'^cumulative-vs-date-chart/$', views.cumulative_vs_date_chart, name='cumulative-vs-date-chart'),
    # url(r'^cumulative-vs-date-chart/2/$', views.cumulative_vs_date_chart, name='cumulative-vs-date-chart'),
    url(r'^cumulative-rev-exp-chart/$', views.revenues_and_expenses_from_journal, name='cumulative-rev-exp-chart'),
    url(r'^chart-of-accounts/$', views.chart_of_accounts, name='chart-of-accounts'),
    url(r'^cash-balances-vs-time/$', views.cash_balances_vs_time, name='cash-balances-vs-time'),
    url(r'^items-needing-attn/$', views.items_needing_attn, name='items-needing-attn'),

    # Webhooks for Payment Processors
    url(r'^squareup/$', views.squareup_webhook, name='squareup-webhook'),

    # DJANGO REST FRAMEWORK API
    url(r'^', include(router.urls)),
]
