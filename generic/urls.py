from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^initialize', 'generic.views.initialize'),
    url(r'^payment', 'generic.views.payment'),
)
