# pylint: disable=invalid-name
"""
    Define url structure
"""
from django.conf.urls import url
from . import views

app_name = 'users'

urlpatterns = [
    url(r'^login$', views.perform_login, name='perform_login'),
    url(r'^logout$', views.perform_logout, name='perform_logout'),
]
