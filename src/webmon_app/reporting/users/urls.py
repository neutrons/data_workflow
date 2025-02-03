# pylint: disable=invalid-name
"""
Define url structure
"""
from django.urls import re_path
from . import views

app_name = "users"

urlpatterns = [
    re_path(r"^login$", views.perform_login, name="perform_login"),
    re_path(r"^logout$", views.perform_logout, name="perform_logout"),
]
