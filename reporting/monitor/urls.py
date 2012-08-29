from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^(?P<instrument>[\w]+)/$', 'monitor.views.live_instrument'),
    url(r'^(?P<instrument>[\w]+)/(?P<parameter>[\w\- ]+)/$', 'monitor.views.live_parameter'),
)
