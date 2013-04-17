from report.models import DataRun, StatusQueue, RunStatus, WorkflowSummary, IPTS, Instrument
from report.models import Information, Error, Task
from django.contrib import admin

def reduction_not_needed(modeladmin, request, queryset):
    queryset.update(reduction_needed=False)
reduction_not_needed.short_description = "Mark selected runs as not needing reduction"

def reduction_needed(modeladmin, request, queryset):
    queryset.update(reduction_needed=True)
reduction_needed.short_description = "Mark selected runs needing reduction"

class DataRunAdmin(admin.ModelAdmin):
    list_filter = ('instrument_id', 'ipts_id')
    list_display = ('id', 'run_number', 'instrument_id', 'ipts_id', 'file', 'created_on')

class IPTSAdmin(admin.ModelAdmin):
    list_display = ('expt_name', 'created_on', 'show_instruments')
    search_fields = ['instruments__name']
    
    def show_instruments(self, ipts):
        instruments = [str(i) for i in ipts.instruments.all()]
        return ', '.join(instruments)
    show_instruments.short_description = "Instruments"

class RunStatusAdmin(admin.ModelAdmin):
    list_filter = ('run_id__instrument_id', 'queue_id')
    list_display = ('id', 'run_id', 'queue_id', 'created_on')
    search_fields = ['run_id__run_number']

class InformationAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_status_id', 'description')
    search_fields = ['description']
    
class ErrorAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_status_id', 'description')
    search_fields = ['description']
    
class StatusQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_workflow_input')
    list_filter = ('is_workflow_input',)
    
class WorkflowSummaryAdmin(admin.ModelAdmin):
    list_filter = ('run_id__instrument_id', 'complete', 'catalog_started', 'cataloged',
                    'reduction_needed', 'reduction_started', 'reduced', 
                    'reduction_cataloged', 'reduction_catalog_started')
    list_display = ('run_id', 'complete', 'catalog_started', 'cataloged',
                    'reduction_needed', 'reduction_started', 'reduced', 
                    'reduction_cataloged', 'reduction_catalog_started')
    search_fields = ['run_id__run_number']
    actions = [reduction_not_needed, reduction_needed]
        
class TaskAdmin(admin.ModelAdmin):
    list_filter = ('instrument_id', 'input_queue_id')
    list_display = ('id', 'instrument_id', 'input_queue_id', 'task_class',
                    'task_queues', 'success_queues')
    search_fields = ['instrument_id__name', 'input_queue_id__name']
    
admin.site.register(DataRun, DataRunAdmin)
admin.site.register(StatusQueue, StatusQueueAdmin)
admin.site.register(RunStatus, RunStatusAdmin)
admin.site.register(WorkflowSummary, WorkflowSummaryAdmin)
admin.site.register(IPTS, IPTSAdmin)
admin.site.register(Instrument)
admin.site.register(Information, InformationAdmin)
admin.site.register(Error, ErrorAdmin)
admin.site.register(Task, TaskAdmin)
