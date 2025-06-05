from django.urls import path

from . import views

app_name = "metrics"

urlpatterns = [
    path("", views.metrics, name="metrics"),
    path("workflow_diagnostics/", views.workflow_diagnostics, name="workflow_diagnostics"),
    path("postprocessing_diagnostics/", views.postprocessing_diagnostics, name="postprocessing_diagnostics"),
    path("instrument_status/", views.instrument_status, name="instrument_status"),
    path("run_statuses/", views.run_statuses, name="run_statuses"),
    path("run_statuses/<int:minutes>/", views.run_statuses, name="run_statuses"),
]
