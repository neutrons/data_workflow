# pylint: disable=invalid-name, line-too-long
"""
    Define url structure
"""
from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required

from django.contrib import admin
admin.autodiscover()
admin.site.login = login_required(admin.site.login)

urlpatterns = [
    url(r'^$', include('dasmon.urls')),
    url(r'^report/', include('report.urls', namespace='report')),
    url(r'^dasmon/', include('dasmon.urls', namespace='dasmon')),
    url(r'^reduction/', include('reduction.urls', namespace='reduction')),
    url(r'^pvmon/', include('pvmon.urls', namespace='pvmon')),
    url(r'^files/', include('file_handling.urls', namespace='file_handling')),
    url(r'^users/', include('users.urls', namespace='users')),
    url(r'^database/', include(admin.site.urls)),
]
