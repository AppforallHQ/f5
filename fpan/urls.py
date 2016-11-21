from django.conf import settings
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from rest_framework import routers
import apiv1.views
import apiv2.urls
import generic.urls
import plans.urls

import analytics
import os

from .env import *

if not os.environ.get('DEVELOPMENT', False):
    from .prod_env import *

analytics.write_key = ANALYTICS_API  

router = routers.DefaultRouter()
router.register(r'subscriptions', apiv1.views.SubscriptionViewSet)
router.register(r'invoices', apiv1.views.InvoiceViewSet)
router.register(r'plans', apiv1.views.PlanViewSet)
router.register(r'bankpayment', apiv1.views.BankPaymentViewSet)
router.register(r'settings', apiv1.views.SettingsViewSet)

urlpatterns = patterns('',
    url(r'^fpan/invoices/pay/(?P<gateway>.*)', 'plans.views.invoice_checkout', name="invoice.checkout"),
    url(r'^fpan/invoices/(?P<gateway>.*)/result', 'plans.views.invoice_payment_result', name="invoice.payment_result"),

    url(r'^fpan/api/v1/', include(router.urls)),
    
    url(r'^fpan/api/v2/', include(apiv2.urls)),
    url(r'^fpan/api/generic/', include(generic.urls)),
    url(r'^fpan/api/plans/', include(plans.urls)),
    url(r'^fpan/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^fpan/admin/', include(admin.site.urls)),
    url(r'', include('tokenapi.urls')),
)
