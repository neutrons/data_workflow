#pylint: disable=invalid-name, line-too-long
"""
    Define url structure
"""
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$',                                                      views.summary,                      name='summary'),
    url(r'^processing$',                                            views.processing_admin,             name='processing_admin'),
    url(r'^(?P<instrument>[\w]+)/$',                                views.instrument_summary,           name='instrument_summary'),
    url(r'^(?P<instrument>[\w]+)/update/$',                         views.get_instrument_update,        name='get_instrument_update'),
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/$',                views.detail,                       name='detail'),
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/reduce/$',         views.submit_for_reduction,         name='submit_for_reduction'),
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/catalog/$',        views.submit_for_cataloging,        name='submit_for_cataloging'),
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/postprocess/$',    views.submit_for_post_processing,   name='submit_for_post_processing'),
    url(r'^(?P<instrument>[\w]+)/experiment/(?P<ipts>[\w\-\.]+)/update/$', views.get_experiment_update, name='get_experiment_update'),
    url(r'^(?P<instrument>[\w]+)/experiment/(?P<ipts>[\w\-\.]+)/$', views.ipts_summary,                 name='ipts_summary'),
    url(r'^(?P<instrument>[\w]+)/errors/$',                         views.live_errors,                  name='live_errors'),
    url(r'^(?P<instrument>[\w]+)/errors/update$',                   views.get_error_update,             name='get_error_update'),
]
