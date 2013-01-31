from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'report.views.summary', name='summary'),
    url(r'^(?P<instrument>[A-Za-z]+)/$', 'report.views.instrument_summary'),
    url(r'^(?P<instrument>[A-Za-z]+)/update/$', 'report.views.get_instrument_update'),
    url(r'^(?P<instrument>[A-Za-z]+)/(?P<run_id>\d+)/$', 'report.views.detail'),
    url(r'^(?P<instrument>[A-Za-z]+)/experiment/(?P<ipts>[\w\-]+)/update/$', 'report.views.get_experiment_update'),
    url(r'^(?P<instrument>[A-Za-z]+)/experiment/(?P<ipts>[\w\-]+)/$', 'report.views.ipts_summary'),
)
