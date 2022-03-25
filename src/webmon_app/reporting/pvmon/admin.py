from reporting.pvmon.models import PVName, PV, PVCache, PVString, PVStringCache, MonitoredVariable
from reporting.report.models import Instrument
from reporting.dasmon.models import ActiveInstrument
from django.contrib import admin
from django.contrib.admin.helpers import ActionForm
from django.shortcuts import get_object_or_404
from django import forms
import datetime


def add_monitored(modeladmin, request, queryset):
    """
    Action used to easily add a monitored variable by typing its name
    instead of browsing through a long list of entries.
    """
    pv_name = get_object_or_404(PVName, name=request.POST["pv_name"])
    instrument_id = get_object_or_404(Instrument, name=request.POST["instrument"].lower())
    m = MonitoredVariable(instrument=instrument_id, pv_name=pv_name)
    m.save()


add_monitored.short_description = "Add monitored"


class UpdateActionForm(ActionForm):
    instrument = forms.ChoiceField(required=True, choices=[])
    pv_name = forms.CharField(required=True, initial="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the list of available instruments
        instruments = [
            (str(i), str(i)) for i in Instrument.objects.all().order_by("name") if ActiveInstrument.objects.is_alive(i)
        ]
        self.fields["instrument"].choices = instruments


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
    action_form = UpdateActionForm
    actions = [add_monitored]


admin.site.register(PVName, PVNameAdmin)
admin.site.register(PV, PVAdmin)
admin.site.register(PVCache, PVAdmin)
admin.site.register(PVString, PVAdmin)
admin.site.register(PVStringCache, PVAdmin)
admin.site.register(MonitoredVariable, MonitoredVariableAdmin)
