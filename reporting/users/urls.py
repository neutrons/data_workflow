from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^login$', 'users.views.perform_login'),
    url(r'^logout$', 'users.views.perform_logout'),
)
