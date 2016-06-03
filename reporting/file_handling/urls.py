#pylint: disable=invalid-name, line-too-long
"""
    Define url structure
"""
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/submit_reduced/$', views.upload_image, name='upload_image'),
]
