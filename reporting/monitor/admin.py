from monitor.models import Parameter, ReportedValue
from django.contrib import admin

class ReportedValueAdmin(admin.ModelAdmin):
    list_display = ('instrument_id', 'parameter_id', 'value', 'timestamp')
    
admin.site.register(Parameter)
admin.site.register(ReportedValue, ReportedValueAdmin)

