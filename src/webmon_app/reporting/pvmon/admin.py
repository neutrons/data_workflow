from django.contrib import admin

from reporting.pvmon.models import PV, MonitoredVariable, PVCache, PVName, PVStringCache


class PVAdmin(admin.ModelAdmin):
    list_filter = ("instrument", "name", "status")
    list_display = (
        "id",
        "instrument",
        "name",
        "value",
        "status",
        "timestamp",
    )


class PVNameAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "monitored")
    list_editable = ("monitored",)


class MonitoredVariableAdmin(admin.ModelAdmin):
    list_display = ("id", "instrument", "pv_name", "rule_name")


admin.site.register(PVName, PVNameAdmin)
admin.site.register(PV, PVAdmin)
admin.site.register(PVCache, PVAdmin)
admin.site.register(PVStringCache, PVAdmin)
admin.site.register(MonitoredVariable, MonitoredVariableAdmin)
