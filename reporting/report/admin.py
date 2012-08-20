from report.models import DataRun, StatusQueue, RunStatus, WorkflowSummary, IPTS, Instrument
from django.contrib import admin

class DataRunAdmin(admin.ModelAdmin):
    list_display = ('run_number', 'instrument_id', 'ipts_id', 'file')

class RunStatusAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'queue_id')

admin.site.register(DataRun, DataRunAdmin)
admin.site.register(StatusQueue)
admin.site.register(RunStatus, RunStatusAdmin)
admin.site.register(WorkflowSummary)
admin.site.register(IPTS)
admin.site.register(Instrument)
