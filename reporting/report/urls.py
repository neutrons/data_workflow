from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'report.views.summary', name='summary'),
    url(r'^(?P<instrument>[A-Za-z]+)/$', 'report.views.instrument_summary'),
    url(r'^(?P<instrument>[A-Za-z]+)/(?P<run_id>\d+)/$', 'report.views.detail'),
    url(r'^(?P<instrument>[A-Za-z]+)/IPTS/(?P<ipts>\d+)/$', 'report.views.ipts_summary'),
)
