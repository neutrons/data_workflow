from report.models import DataRun, StatusQueue, RunStatus, WorkflowSummary, IPTS, Instrument
from report.models import Information, Error, Task
from django.contrib import admin

class DataRunAdmin(admin.ModelAdmin):
    list_display = ('run_number', 'instrument_id', 'ipts_id', 'file')

class RunStatusAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'queue_id')

class InformationAdmin(admin.ModelAdmin):
    list_display = ('run_status_id', 'description')

class ErrorAdmin(admin.ModelAdmin):
    list_display = ('run_status_id', 'description')
    
class StatusQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_workflow_input')
    
class WorkflowSummaryAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'complete', 'catalog_started', 'cataloged',
                    'reduction_needed', 'reduction_started', 'reduced', 
                    'reduction_cataloged', 'reduction_catalog_started')
    search_fields = ['run_id__run_number']
        
class TaskAdmin(admin.ModelAdmin):
    list_display = ('instrument_id', 'input_queue_id', 'task_class',
                    'task_queues', 'success_queues')
    search_fields = ['instrument_id__name']
    
admin.site.register(DataRun, DataRunAdmin)
admin.site.register(StatusQueue, StatusQueueAdmin)
admin.site.register(RunStatus, RunStatusAdmin)
admin.site.register(WorkflowSummary, WorkflowSummaryAdmin)
admin.site.register(IPTS)
admin.site.register(Instrument)
admin.site.register(Information, InformationAdmin)
admin.site.register(Error, ErrorAdmin)
admin.site.register(Task, TaskAdmin)
