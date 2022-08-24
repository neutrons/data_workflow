from reporting.pvmon.models import PVName, PV, PVCache, PVString, PVStringCache, MonitoredVariable
from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
import datetime


class PVNameCharField(forms.fields.CharField):
    def to_python(self, value):
        if isinstance(value, PVName):
            return value

        if value is None:
            return value

        try:
            return PVName.objects.get(name=value)
        except PVName.DoesNotExist:
            raise ValidationError("PvName does not exist")


class AddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pv_name"] = PVNameCharField()

    class Meta:
        model = MonitoredVariable
        exclude = ()


class PVAdmin(admin.ModelAdmin):
    list_filter = ("instrument", "name", "status")
    list_display = (
        "id",
        "instrument",
        "name",
        "value",
        "status",
        "update_time",
        "get_timestamp",
    )

    def get_timestamp(self, pv):
        return datetime.datetime.fromtimestamp(pv.update_time)

    get_timestamp.short_description = "Time"


class PVNameAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "monitored")
    list_editable = ("monitored",)


class MonitoredVariableAdmin(admin.ModelAdmin):
    list_display = ("id", "instrument", "pv_name", "rule_name")
    list_editable = ("pv_name", "rule_name")
    form = AddForm


admin.site.register(PVName, PVNameAdmin)
admin.site.register(PV, PVAdmin)
admin.site.register(PVCache, PVAdmin)
admin.site.register(PVString, PVAdmin)
admin.site.register(PVStringCache, PVAdmin)
admin.site.register(MonitoredVariable, MonitoredVariableAdmin)
