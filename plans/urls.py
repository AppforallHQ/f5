from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^invite_promo', 'plans.views.invite_promo'),
)
