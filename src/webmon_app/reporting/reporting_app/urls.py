# pylint: disable=invalid-name, line-too-long
"""
Define url structure
"""
from django.urls import include, path
from django.contrib.auth.decorators import login_required

from django.views.generic.base import RedirectView

from django.contrib import admin

admin.autodiscover()
admin.site.login = login_required(admin.site.login)

urlpatterns = [
    path("", RedirectView.as_view(url="/dasmon/")),
    path("report/", include("reporting.report.urls", namespace="report")),
    path("dasmon/", include("reporting.dasmon.urls", namespace="dasmon")),
    path("reduction/", include("reporting.reduction.urls", namespace="reduction")),
    path("pvmon/", include("reporting.pvmon.urls", namespace="pvmon")),
    path("users/", include("reporting.users.urls", namespace="users")),
    path("metrics/", include("reporting.metrics.urls", namespace="metrics")),
    path("database/", admin.site.urls),
    path("ht/", include("health_check.urls")),
]
