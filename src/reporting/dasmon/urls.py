# pylint: disable=invalid-name, line-too-long
"""
    Define url structure
"""
from django.conf.urls import url
from . import views

app_name = 'dasmon'

urlpatterns = [
    url(r'^$', views.dashboard_simple, name='dashboard'),
    url(r'^update/$', views.summary_update, name='summary_update'),
    url(r'^summary/$', views.run_summary, name='run_summary'),
    url(r'^dashboard/$', views.dashboard, name='dashboard_complete'),
    url(r'^dashboard/update/$', views.dashboard_update, name='dashboard_update'),
    url(r'^expert/$', views.expert_status, name='expert'),
    url(r'^summary/update/$', views.run_summary_update, name='run_summary_update'),
    url(r'^user_help/', views.user_help, name='user_help'),
    url(r'^notifications/', views.notifications, name='notifications'),
    url(r'^(?P<instrument>[\w]+)/$', views.live_monitor, name='live_monitor'),
    url(r'^(?P<instrument>[\w]+)/runs/$', views.live_runs, name='live_runs'),
    url(r'^(?P<instrument>[\w]+)/update/$', views.get_update, name='get_update'),
    url(r'^(?P<instrument>[\w]+)/diagnostics/$', views.diagnostics, name='diagnostics'),
    url(r'^(?P<instrument>[\w]+)/signals/$', views.get_signal_table, name='get_signal_table'),
    url(r'^(?P<instrument>[\w]+)/signals/ack/(?P<sig_id>\d+)/$', views.acknowledge_signal, name='acknowledge_signal'),
    url(r'^(?P<instrument>[\w]+)/legacy/$', views.legacy_monitor, name='legacy_monitor'),
    url(r'^(?P<instrument>[\w]+)/legacy/update/$', views.get_legacy_data, name='get_legacy_data'),
]
