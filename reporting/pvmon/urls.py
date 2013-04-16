from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^(?P<instrument>[\w]+)/$', 'pvmon.views.pv_monitor'),
    url(r'^(?P<instrument>[\w]+)/update/$', 'pvmon.views.get_update'),
)
