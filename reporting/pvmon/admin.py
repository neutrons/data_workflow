from pvmon.models import PVName, PV
from django.contrib import admin
import datetime
    
class PVAdmin(admin.ModelAdmin):
    

    list_filter = ('name', 'status')
    list_display = ('name', 'value', 'status', 'update_time', 'get_timestamp')

    def get_timestamp(self, pv):
        return datetime.datetime.fromtimestamp(pv.update_time)
    get_timestamp.short_description = "Time"

    
admin.site.register(PVName)
admin.site.register(PV, PVAdmin)


