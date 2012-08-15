from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'report.views.summary', name='summary'),
    url(r'(?P<run_id>\d+)/$', 'report.views.detail', name='detail'),
)
