from dasmon.models import StatusVariable, Parameter, StatusCache, ActiveInstrument, Signal
from django.contrib import admin

class StatusVariableAdmin(admin.ModelAdmin):
    list_filter = ('instrument_id', 'key_id')
    list_display = ('id', 'instrument_id', 'key_id', 'value', 'format_time')
    def format_time(self, obj):
        return obj.timestamp.strftime('%d %b, %Y %H:%M:%S')
    format_time.short_description = 'Time'


class ParameterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'monitored')
    list_editable = ('monitored',)

class ActiveInstrumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'instrument_id', 'is_alive', 'is_adara')
    list_editable = ('is_alive', 'is_adara')
    
class SignalAdmin(admin.ModelAdmin):
    list_display = ('id', 'instrument_id', 'name', 'message', 'level', 'timestamp')
    
admin.site.register(StatusVariable, StatusVariableAdmin)
admin.site.register(Parameter, ParameterAdmin)
admin.site.register(StatusCache, StatusVariableAdmin)
admin.site.register(ActiveInstrument, ActiveInstrumentAdmin)
admin.site.register(Signal, SignalAdmin)
