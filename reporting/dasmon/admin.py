from dasmon.models import StatusVariable, Parameter, StatusCache
from django.contrib import admin

class StatusVariableAdmin(admin.ModelAdmin):
    list_filter = ('instrument_id', 'key_id')
    list_display = ('id', 'instrument_id', 'key_id', 'value', 'timestamp')

class ParameterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'monitored')
    list_editable = ('monitored',)

    
admin.site.register(StatusVariable, StatusVariableAdmin)
admin.site.register(Parameter, ParameterAdmin)
admin.site.register(StatusCache, StatusVariableAdmin)


