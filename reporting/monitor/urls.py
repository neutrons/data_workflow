from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^(?P<instrument>[\w]+)/$', 'monitor.views.live_errors'),
    url(r'^(?P<instrument>[\w]+)/update/$', 'monitor.views.get_update'),
)
