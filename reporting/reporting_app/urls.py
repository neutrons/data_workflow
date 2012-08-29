from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', include('report.urls')),
    url(r'^report/', include('report.urls')),
    url(r'^monitor/', include('monitor.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
