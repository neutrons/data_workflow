# pylint: disable=invalid-name, line-too-long
"""
    Define url structure
"""
# from django.conf.urls import include, re_path
from django.urls import include, path
from django.contrib.auth.decorators import login_required

from django.views.generic.base import RedirectView

from django.contrib import admin
admin.autodiscover()
admin.site.login = login_required(admin.site.login)

urlpatterns = [
    path('', RedirectView.as_view(url='/dasmon/')),
    path('report/', include('report.urls', namespace='report')),
    path('dasmon/', include('dasmon.urls', namespace='dasmon')),
    path('reduction/', include('reduction.urls', namespace='reduction')),
    path('pvmon/', include('pvmon.urls', namespace='pvmon')),
    path('files/', include('file_handling.urls', namespace='file_handling')),
    path('users/', include('users.urls', namespace='users')),
    path('database/', admin.site.urls),
]
