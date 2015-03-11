from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'dasmon.views.dashboard'),
    url(r'^update/$', 'dasmon.views.summary_update'),
    url(r'^summary/$', 'dasmon.views.run_summary', name='dasmon_summary'),
    url(r'^dashboard/$', 'dasmon.views.dashboard', name='dasmon_dashboard'),
    url(r'^dashboard/update/$', 'dasmon.views.dashboard_update'),
    url(r'^summary/update/$', 'dasmon.views.run_summary_update', name='dasmon_summary_update'),
    url(r'^user_help/', 'dasmon.views.help'),
    url(r'^notifications/', 'dasmon.views.notifications'),
    url(r'^(?P<instrument>[\w]+)/$', 'dasmon.views.live_monitor'),
    url(r'^(?P<instrument>[\w]+)/runs/$', 'dasmon.views.live_runs', name='dasmon_live_runs'),
    url(r'^(?P<instrument>[\w]+)/update/$', 'dasmon.views.get_update'),
    url(r'^(?P<instrument>[\w]+)/diagnostics/$', 'dasmon.views.diagnostics'),
    url(r'^(?P<instrument>[\w]+)/signals/$', 'dasmon.views.get_signal_table'),
    url(r'^(?P<instrument>[\w]+)/signals/ack/(?P<sig_id>\d+)/$', 'dasmon.views.acknowledge_signal'),
    url(r'^(?P<instrument>[\w]+)/legacy/$', 'dasmon.views.legacy_monitor'),
    url(r'^(?P<instrument>[\w]+)/legacy/update/$', 'dasmon.views.get_legacy_data'),
    
)
