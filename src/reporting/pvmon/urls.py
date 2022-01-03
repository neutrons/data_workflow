# pylint: disable=invalid-name, line-too-long
"""
    Define url structure
"""
from django.conf.urls import url
from . import views

app_name = 'pvmon'

urlpatterns = [
    url(r'^(?P<instrument>[\w]+)/$', views.pv_monitor, name='pv_monitor'),
    url(r'^(?P<instrument>[\w]+)/update/$', views.get_update, name='get_update'),
]
