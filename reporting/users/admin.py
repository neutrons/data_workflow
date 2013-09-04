from users.models import PageView, DeveloperNode
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
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
        if self.value() == 'non_developers':
            try:
                nodes = DeveloperNode.objects.all().values_list('ip', flat=True)
                return queryset.exclude(user__is_staff=True).exclude(ip__in=nodes)
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

class DeveloperNodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ip', 'get_host')
    
    def get_host(self, view):
        try:
            return socket.gethostbyaddr(view.ip)[0]
        except:
            return "unknown"
    get_host.short_description = "Host"
    
class SNSUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'get_groups', 'is_staff', 'is_superuser')
    
    def get_groups(self, user):
        groups = []
        for g in user.groups.all():
            groups.append(g.name)
        return ', '.join(groups)
    get_groups.short_description = "Groups"

admin.site.unregister(User)
admin.site.register(User, SNSUserAdmin)
admin.site.register(PageView, PageViewAdmin)
admin.site.register(DeveloperNode, DeveloperNodeAdmin)




