# pylint: disable=invalid-name, line-too-long
"""
Define url structure
"""

from django.urls import re_path

from . import views

app_name = "pvmon"

urlpatterns = [
    re_path(r"^(?P<instrument>[\w]+)/$", views.pv_monitor, name="pv_monitor"),
    re_path(r"^(?P<instrument>[\w]+)/update/$", views.get_update, name="get_update"),
]
