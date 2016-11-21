from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^beginsubscription', 'apiv2.views.beginsubscription'),
    url(r'^applypromocode', 'apiv2.views.applypromocode'),
    url(r'^startpayment', 'apiv2.views.startpayment'),
    url(r'^error_page', 'apiv2.views.general_error_page'),
    url(r'^alter_user', 'apiv2.views.alter_user'),
    url(r'^invoicepayment', 'apiv2.views.invoice_payment'),
    url(r'^begininvoicepayment', 'apiv2.views.begin_invoice_payment'),
    url(r'^change_plan', 'apiv2.views.change_plan'),
    url(r'^block_device_switch', 'apiv2.views.block_device_switch'),
    url(r'^create_gift', 'apiv2.views.create_gift'),
    url(r'^gift_start_payment', 'apiv2.views.gift_start_payment'),
    url(r'^gen_promo', 'apiv2.views.generate_promo_code'),
    url(r'^check_promo', 'apiv2.views.check_promo'),
    url(r'^report', 'apiv2.views.reporter'),
)
