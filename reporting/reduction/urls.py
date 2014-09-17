from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^(?P<instrument>[\w]+)/$', 'reduction.views.configuration', name='reduction_configuration'),
    url(r'^(?P<instrument>[\w]+)/change$', 'reduction.views.configuration_change', name='reduction_configuration_change'),
)