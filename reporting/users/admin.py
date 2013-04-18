from users.models import PageView
from django.contrib import admin
import socket

class PageViewAdmin(admin.ModelAdmin):
    list_filter = ('user', 'view')
    list_display = ('user', 'view', 'ip', 'get_host', 'path', 'timestamp')

    def get_host(self, view):
        try:
            return socket.gethostbyaddr(view.ip)[0]
        except:
            return "unknown"
    get_host.short_description = "Host"


admin.site.register(PageView, PageViewAdmin)



