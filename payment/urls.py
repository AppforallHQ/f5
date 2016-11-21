from django.conf.urls.defaults import patterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = patterns(
    'apps.payment.views',
    # (r'^$', ''),
)
urlpatterns += staticfiles_urlpatterns()
