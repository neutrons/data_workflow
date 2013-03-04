from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from django.contrib import admin
admin.autodiscover()
admin.site.login = login_required(admin.site.login)

urlpatterns = patterns('',
    url(r'^$', include('report.urls')),
    url(r'^report/', include('report.urls')),
    url(r'^monitor/', include('monitor.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^database/', include(admin.site.urls)),
)
