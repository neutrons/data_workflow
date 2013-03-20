from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^(?P<instrument>[\w]+)/$', 'dasmon.views.live_monitor'),
    url(r'^(?P<instrument>[\w]+)/runs$', 'dasmon.views.live_runs'),
    url(r'^(?P<instrument>[\w]+)/update/$', 'dasmon.views.get_update'),
)
