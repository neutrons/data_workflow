from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/submit_reduced/$', 'file_handling.views.upload_image'),
)
