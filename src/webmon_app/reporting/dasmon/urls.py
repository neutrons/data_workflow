# pylint: disable=invalid-name, line-too-long
"""
Define url structure
"""

from django.urls import re_path

from . import views

app_name = "dasmon"

urlpatterns = [
    re_path(r"^$", views.dashboard_simple, name="dashboard"),
    re_path(r"^update/$", views.summary_update, name="summary_update"),
    re_path(r"^summary/$", views.run_summary, name="run_summary"),
    re_path(r"^dashboard/$", views.dashboard, name="dashboard_complete"),
    re_path(r"^dashboard/update/$", views.dashboard_update, name="dashboard_update"),
    re_path(r"^expert/$", views.expert_status, name="expert"),
    re_path(r"^summary/update/$", views.run_summary_update, name="run_summary_update"),
    re_path(r"^user_help/", views.user_help, name="user_help"),
    re_path(r"^notifications/", views.notifications, name="notifications"),
    re_path(r"^(?P<instrument>[\w]+)/$", views.live_monitor, name="live_monitor"),
    re_path(r"^(?P<instrument>[\w]+)/runs/$", views.live_runs, name="live_runs"),
    re_path(r"^(?P<instrument>[\w]+)/update/$", views.get_update, name="get_update"),
    re_path(r"^(?P<instrument>[\w]+)/diagnostics/$", views.diagnostics, name="diagnostics"),
    re_path(
        r"^(?P<instrument>[\w]+)/signals/$",
        views.get_signal_table,
        name="get_signal_table",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/signals/ack/(?P<sig_id>\d+)/$",
        views.acknowledge_signal,
        name="acknowledge_signal",
    ),
]
