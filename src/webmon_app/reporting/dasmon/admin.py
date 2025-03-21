from reporting.dasmon.models import (
    StatusVariable,
    Parameter,
    StatusCache,
    ActiveInstrument,
    Signal,
    UserNotification,
)
from django.contrib import admin
import datetime
import logging


class StatusVariableAdmin(admin.ModelAdmin):
    list_filter = ("instrument_id", "key_id")
    list_display = ("id", "instrument_id", "key_id", "value", "timestamp", "msg_time")

    def msg_time(self, obj):
        if obj.key_id.name == "timestamp":
            try:
                return datetime.datetime.fromtimestamp(int(obj.value))
            except:  # noqa: E722
                logging.exception("")
                return "error"
        return "-"


class ParameterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "monitored")
    list_editable = ("monitored",)


class ActiveInstrumentAdmin(admin.ModelAdmin):
    list_display = ("id", "instrument_id", "is_alive", "is_adara")
    list_editable = ("is_alive", "is_adara")


class SignalAdmin(admin.ModelAdmin):
    list_display = ("id", "instrument_id", "name", "message", "level", "timestamp")


class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "email")


admin.site.register(StatusVariable, StatusVariableAdmin)
admin.site.register(Parameter, ParameterAdmin)
admin.site.register(StatusCache, StatusVariableAdmin)
admin.site.register(ActiveInstrument, ActiveInstrumentAdmin)
admin.site.register(Signal, SignalAdmin)
admin.site.register(UserNotification, UserNotificationAdmin)
