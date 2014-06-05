from dasmon.models import StatusVariable, Parameter, StatusCache, ActiveInstrument, Signal, LegacyURL
from django.contrib import admin

class StatusVariableAdmin(admin.ModelAdmin):
    list_filter = ('instrument_id', 'key_id')
    list_display = ('id', 'instrument_id', 'key_id', 'value', 'timestamp')

class ParameterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'monitored')
    list_editable = ('monitored',)

class ActiveInstrumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'instrument_id', 'is_alive', 'is_adara')
    list_editable = ('is_alive', 'is_adara')
    
class SignalAdmin(admin.ModelAdmin):
    list_display = ('id', 'instrument_id', 'name', 'message', 'level', 'timestamp')
    
class LegacyURLAdmin(admin.ModelAdmin):
    list_display = ('id', 'instrument_id', 'url', 'long_name')
    
admin.site.register(StatusVariable, StatusVariableAdmin)
admin.site.register(Parameter, ParameterAdmin)
admin.site.register(StatusCache, StatusVariableAdmin)
admin.site.register(ActiveInstrument, ActiveInstrumentAdmin)
admin.site.register(Signal, SignalAdmin)
admin.site.register(LegacyURL, LegacyURLAdmin)
