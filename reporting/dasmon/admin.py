from dasmon.models import StatusVariable, Parameter, StatusCache
from django.contrib import admin

class StatusVariableAdmin(admin.ModelAdmin):
    list_display = ('instrument_id', 'key_id', 'value', 'timestamp')

class StatusCacheAdmin(admin.ModelAdmin):
    list_display = ('instrument_id', 'key_id', 'value', 'timestamp')

class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'monitored')

    
admin.site.register(StatusVariable, StatusVariableAdmin)
admin.site.register(Parameter, ParameterAdmin)
admin.site.register(StatusCache, StatusCacheAdmin)


