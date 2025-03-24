# pylint: disable=invalid-name, line-too-long
"""
Define url structure
"""
from django.urls import re_path
from . import views

app_name = "report"

urlpatterns = [
    re_path(r"^$", views.summary, name="summary"),
    re_path(r"^processing$", views.processing_admin, name="processing_admin"),
    re_path(r"^(?P<instrument>[\w]+)/$", views.instrument_summary, name="instrument_summary"),
    re_path(
        r"^(?P<instrument>[\w]+)/datatables/$",
        views.instrument_summary_datatables,
        name="instrument_summary_datatables",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/update/$",
        views.get_instrument_update,
        name="get_instrument_update",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/update/datatables/$",
        views.get_instrument_update_datatables,
        name="get_instrument_update_datatables",
    ),
    re_path(r"^(?P<instrument>[\w]+)/(?P<run_id>\d+)/$", views.detail, name="detail"),
    re_path(
        r"^(?P<instrument>[\w]+)/(?P<run_id>\d+)/data/$",
        views.download_reduced_data,
        name="download_reduced_data",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/(?P<run_id>\d+)/reduce/$",
        views.submit_for_reduction,
        name="submit_for_reduction",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/(?P<run_id>\d+)/catalog/$",
        views.submit_for_cataloging,
        name="submit_for_cataloging",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/(?P<run_id>\d+)/postprocess/$",
        views.submit_for_post_processing,
        name="submit_for_post_processing",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/experiment/(?P<ipts>[\w\-\.]+)/update/$",
        views.get_experiment_update,
        name="get_experiment_update",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/experiment/(?P<ipts>[\w\-\.]+)/$",
        views.ipts_summary,
        name="ipts_summary",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/experiment/(?P<ipts>[\w\-\.]+)/datatables/$",
        views.ipts_summary_datatables,
        name="ipts_summary_datatables",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/experiment/(?P<ipts>[\w\-\.]+)/run_list/$",
        views.ipts_summary_run_list,
        name="ipts_summary_run_list",
    ),
    re_path(r"^(?P<instrument>[\w]+)/errors/$", views.live_errors, name="live_errors"),
    re_path(
        r"^(?P<instrument>[\w]+)/errors/update$",
        views.get_error_update,
        name="get_error_update",
    ),
]
