# pylint: disable=invalid-name, line-too-long
"""
    Define url structure
"""
from django.conf.urls import re_path
from . import views

app_name = "reduction"

urlpatterns = [
    re_path(r"^(?P<instrument>[\w]+)/$", views.configuration, name="configuration"),
    re_path(
        r"^(?P<instrument>[\w]+)/change$",
        views.configuration_change,
        name="configuration_change",
    ),
    re_path(
        r"^(?P<instrument>[\w]+)/update$",
        views.configuration_update,
        name="configuration_update",
    ),
]
