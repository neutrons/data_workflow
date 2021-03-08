#pylint: disable=invalid-name, line-too-long
"""
    Define url structure
"""
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<instrument>[\w]+)/$',       views.configuration,        name='configuration'),
    url(r'^(?P<instrument>[\w]+)/change$', views.configuration_change, name='configuration_change'),
    url(r'^(?P<instrument>[\w]+)/update$', views.configuration_update, name='configuration_update'),
]
