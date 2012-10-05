from report.models import DataRun, StatusQueue, RunStatus, WorkflowSummary, IPTS, Instrument
from report.models import Information, Error
from django.contrib import admin

class DataRunAdmin(admin.ModelAdmin):
    list_display = ('run_number', 'instrument_id', 'ipts_id', 'file')

class RunStatusAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'queue_id')

class InformationAdmin(admin.ModelAdmin):
    list_display = ('run_status_id', 'description')

class ErrorAdmin(admin.ModelAdmin):
    list_display = ('run_status_id', 'description')

admin.site.register(DataRun, DataRunAdmin)
admin.site.register(StatusQueue)
admin.site.register(RunStatus, RunStatusAdmin)
admin.site.register(WorkflowSummary)
admin.site.register(IPTS)
admin.site.register(Instrument)
admin.site.register(Information, InformationAdmin)
admin.site.register(Error, ErrorAdmin)
