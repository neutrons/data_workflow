from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from reporting.dasmon.models import ActiveInstrument, Parameter, StatusCache
from reporting.dasmon.view_util import is_running
from reporting.report.models import DataRun, Information, Instrument, WorkflowSummary
from reporting.report.view_util import is_acquisition_complete


def postprocessing_diagnostics():
    """collect and return Cataloging & Reduction diagnostics"""
    common_services = Instrument.objects.get(name="common")
    agents = []

    for node_prefix in settings.POSTPROCESS_NODE_PREFIX:
        params = Parameter.objects.filter(
            ~Q(name__endswith="_pid"),
            name__startswith=settings.SYSTEM_STATUS_PREFIX + node_prefix,
        )
        for param in params:
            node = param.name.removeprefix(settings.SYSTEM_STATUS_PREFIX)
            info = {"name": node}
            value = StatusCache.objects.filter(instrument_id=common_services, key_id=param).latest("timestamp")
            info["timestamp"] = value.timestamp

            try:
                pid = Parameter.objects.get(name=param.name + "_pid")
                info["PID"] = (
                    StatusCache.objects.filter(instrument_id=common_services, key_id=pid).latest("timestamp").value
                )

            except (Parameter.DoesNotExist, StatusCache.DoesNotExist):
                pass

            try:
                last_status = Information.objects.filter(description=node).latest("id")
                info["last_message"] = str(last_status.run_status_id)
                info["last_message_timestamp"] = last_status.run_status_id.created_on
            except Information.DoesNotExist:
                pass
            agents.append(info)

    return agents


def instrument_status():
    """return map of instrument name to run status"""

    instruments = Instrument.objects.all().order_by("name")
    status = {}

    for instrument_id in instruments:
        if ActiveInstrument.objects.is_alive(instrument_id):
            status[str(instrument_id)] = is_running(instrument_id)

    return status


def run_statuses(minutes=60):
    """Of all the runs created in the last n minutes,
    return the number that are acquiring, complete, incomplete,
    error or unknown along with the total number"""

    runs = DataRun.objects.filter(created_on__gte=timezone.now() - timezone.timedelta(minutes=minutes)).order_by(
        "created_on"
    )

    statuses = {
        "total": len(runs),
        "acquiring": 0,
        "incomplete": 0,
        "complete": 0,
        "error": 0,
        "unknown": 0,
    }

    for run_id in runs:
        try:
            s = WorkflowSummary.objects.get(run_id=run_id)
        except WorkflowSummary.DoesNotExist:
            statuses["unknown"] += 1
            continue

        if not is_acquisition_complete(run_id):
            statuses["acquiring"] += 1
        elif s.complete:
            statuses["complete"] += 1
        elif run_id.last_error() is None:
            statuses["incomplete"] += 1
        else:
            statuses["error"] += 1

    return statuses
