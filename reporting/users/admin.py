from users.models import PageView
from django.contrib import admin
import socket
from django.conf import settings
import logging
import sys

class NonDeveloperUsers(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'User type'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'user_type'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('non_developers', 'Non-developers'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        developer_nodes = None
        developer_ids = None
        if hasattr(settings, "DEVELOPER_NODES"):
            developer_nodes = settings.DEVELOPER_NODES
        if hasattr(settings, "DEVELOPER_IDS"):
            developer_ids = settings.DEVELOPER_IDS
            
        if self.value() == 'non_developers':
            try:
                if developer_ids is not None:
                    queryset = queryset.exclude(user__username__in=developer_ids)
                if developer_nodes is not None:
                    queryset = queryset.exclude(ip__in=developer_nodes)
            except:
                logging.error(sys.exc_value)

        return queryset
 
class PageViewAdmin(admin.ModelAdmin):
    list_filter = ('user', 'view', NonDeveloperUsers)
    list_display = ('user', 'view', 'ip', 'get_host', 'path', 'timestamp')

    def get_host(self, view):
        try:
            return socket.gethostbyaddr(view.ip)[0]
        except:
            return "unknown"
    get_host.short_description = "Host"


admin.site.register(PageView, PageViewAdmin)




