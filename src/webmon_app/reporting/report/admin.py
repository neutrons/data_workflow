from reporting.report.models import (
    DataRun,
    StatusQueue,
    StatusQueueMessageCount,
    RunStatus,
    WorkflowSummary,
    IPTS,
    Instrument,
    InstrumentStatus,
)
from reporting.report.models import Information, Error, Task
from django.contrib import admin


def reduction_not_needed(modeladmin, request, queryset):
    queryset.update(reduction_needed=False)


reduction_not_needed.short_description = "Mark selected runs as not needing reduction"


def reduction_needed(modeladmin, request, queryset):
    queryset.update(reduction_needed=True)


reduction_needed.short_description = "Mark selected runs needing reduction"


def reduction_incomplete(modeladmin, request, queryset):
    queryset.update(complete=False)


reduction_incomplete.short_description = "Mark selected runs as incomplete"


def reduction_complete(modeladmin, request, queryset):
    queryset.update(complete=True)


reduction_complete.short_description = "Mark selected runs as complete"


class DataRunAdmin(admin.ModelAdmin):
    list_filter = ("instrument_id", "ipts_id")
    list_display = (
        "id",
        "run_number",
        "instrument_id",
        "ipts_id",
        "file",
        "created_on",
    )


class IPTSAdmin(admin.ModelAdmin):
    list_display = ("expt_name", "created_on", "show_instruments")
    search_fields = ["instruments__name"]

    def show_instruments(self, ipts):
        instruments = [str(i) for i in ipts.instruments.all()]
        return ", ".join(instruments)

    show_instruments.short_description = "Instruments"


class RunStatusAdmin(admin.ModelAdmin):
    readonly_fields = ("run_id",)
    list_filter = ("run_id__instrument_id", "queue_id")
    list_display = ("id", "run_id", "queue_id", "created_on")
    search_fields = ["run_id__run_number"]


class InformationAdmin(admin.ModelAdmin):
    readonly_fields = ("run_status_id",)
    list_display = ("id", "run_status_id", "time", "description")
    search_fields = ["description"]

    def time(self, obj):
        return obj.run_status_id.created_on


class ErrorAdmin(admin.ModelAdmin):
    readonly_fields = ("run_status_id",)
    list_display = ("id", "run_status_id", "time", "description")
    list_filter = ("run_status_id__run_id__instrument_id",)
    search_fields = ["description"]

    def time(self, obj):
        return obj.run_status_id.created_on


class StatusQueueAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_workflow_input")
    list_filter = ("is_workflow_input",)


class StatusQueueMessageCountAdmin(admin.ModelAdmin):
    list_display = ("id", "queue_id", "message_count", "created_on")
    list_filter = ("queue_id",)


class WorkflowSummaryAdmin(admin.ModelAdmin):
    readonly_fields = ("run_id",)
    list_filter = (
        "run_id__instrument_id",
        "complete",
        "catalog_started",
        "cataloged",
        "reduction_needed",
        "reduction_started",
        "reduced",
        "reduction_cataloged",
        "reduction_catalog_started",
    )
    list_display = (
        "run_id",
        "date",
        "complete",
        "catalog_started",
        "cataloged",
        "reduction_needed",
        "reduction_started",
        "reduced",
        "reduction_cataloged",
        "reduction_catalog_started",
    )
    search_fields = ["run_id__run_number"]
    actions = [
        reduction_not_needed,
        reduction_needed,
        reduction_complete,
        reduction_incomplete,
    ]
    list_editable = ("reduction_needed",)

    def date(self, summary):
        return summary.run_id.created_on.strftime("%y-%m-%d")


class TaskAdmin(admin.ModelAdmin):
    list_filter = ("instrument_id", "input_queue_id")
    list_display = (
        "id",
        "instrument_id",
        "input_queue_id",
        "task_class",
        "task_queues",
        "success_queues",
    )
    search_fields = ["instrument_id__name", "input_queue_id__name"]


class InstrumentStatusAdmin(admin.ModelAdmin):
    readonly_fields = ("last_run_id",)
    list_display = ("id", "instrument_id", "last_run_id")


admin.site.register(DataRun, DataRunAdmin)
admin.site.register(StatusQueue, StatusQueueAdmin)
admin.site.register(StatusQueueMessageCount, StatusQueueMessageCountAdmin)
admin.site.register(RunStatus, RunStatusAdmin)
admin.site.register(WorkflowSummary, WorkflowSummaryAdmin)
admin.site.register(IPTS, IPTSAdmin)
admin.site.register(Instrument)
admin.site.register(Information, InformationAdmin)
admin.site.register(Error, ErrorAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(InstrumentStatus, InstrumentStatusAdmin)
