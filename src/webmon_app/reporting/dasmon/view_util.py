"""
    Status monitor utilities to support 'dasmon' views

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""

from reporting.report.models import Instrument, DataRun, WorkflowSummary, Information
from reporting.dasmon.models import (
    Parameter,
    StatusVariable,
    StatusCache,
    ActiveInstrument,
    Signal,
)
from reporting.pvmon.models import PVCache, PVStringCache, MonitoredVariable
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone, formats
from django.contrib.auth.models import Group
from django.conf import settings
import datetime
import logging
import time
import reporting.report.view_util as report_view_util
import reporting.pvmon.view_util as pvmon_view_util
import reporting.users.view_util as users_view_util

LOGNAME = "dasmon:view_util"


def get_monitor_breadcrumbs(instrument_id, current_view="monitor"):
    """
    Create breadcrumbs for a live monitoring view

    :param instrument_id: Instrument object
    :param current_view: name to give this view
    """
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    if ActiveInstrument.objects.is_alive(instrument_id):
        breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (
            reverse("report:instrument_summary", args=[instrument_id.name]),
            instrument_id.name,
        )
    else:
        breadcrumbs += " &rsaquo; %s" % instrument_id.name
    breadcrumbs += " &rsaquo; %s" % current_view
    return breadcrumbs


def get_cached_variables(instrument_id, monitored_only=False):
    """
    Get cached parameter values for a given instrument

    :param instrument_id: Instrument object
    :param monitored_only: if True, only monitored parameters are returned
    """
    parameter_values = StatusCache.objects.filter(instrument_id=instrument_id).order_by("key_id__name", "-timestamp")
    # Variables that are displayed on top
    top_variables = ["run_number", "proposal_id", "run_title"]
    key_value_pairs = []
    keys_used = set()
    for kvp in parameter_values:

        if kvp.key_id in keys_used:
            # only used the first value for each key, will be ordered newest first
            continue

        keys_used.add(kvp.key_id)

        if kvp.key_id.monitored or monitored_only is False:
            # Exclude top variables
            if monitored_only and str(kvp.key_id) in top_variables:
                continue
            try:
                localtime = timezone.localtime(kvp.timestamp)
            except:  # noqa: E722
                localtime = kvp.timestamp

            # Check whether we have a number
            try:
                float_value = float(kvp.value)
                string_value = "%g" % float_value
            except:  # noqa: E722
                string_value = kvp.value

            # Tweak the title string so we don't have ><
            if str(kvp.key_id) == "run_title":
                string_value = _prune_title_string(string_value)

            variable_dict = {
                "key": str(kvp.key_id),
                "value": string_value,
                "timestamp": formats.localize(localtime),
            }
            key_value_pairs.append(variable_dict)

    return key_value_pairs


def _prune_title_string(value):
    """
    Replace unusual characters in a string.
    This is mostly for run titles which come in from the DAS with weird delimiters.

    :param value: string
    """
    try:
        pruned = value
        if pruned.endswith("><"):
            pruned = pruned[: len(pruned) - 2]
        toks = pruned.split("><")
        if len(toks) > 1:
            comments = "<span style='font-size:small'>%s</span>" % "<br>".join(toks[1:])
            return "%s<br>%s" % (toks[0], comments)
        else:
            return pruned
    except:  # noqa: E722
        return value


def get_latest(instrument_id, key_id):
    """
    Returns the latest entry for a given key on a given instrument

    :param instrument_id: Instrument object
    :param key_id: Parameter object
    """
    # First get it from the cache
    try:
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest("timestamp")
    except StatusCache.DoesNotExist:
        # If that didn't work, get it from the table of values
        try:
            last_value = StatusVariable.objects.filter(instrument_id=instrument_id, key_id=key_id).latest("timestamp")
        except StatusVariable.DoesNotExist:
            # If we don't have any entry yet, just return None
            return None

        # Put the latest value in the cache so we don't have to go through this again
        cached = StatusCache(
            instrument_id=last_value.instrument_id,
            key_id=last_value.key_id,
            value=last_value.value,
            timestamp=last_value.timestamp,
        )
        cached.save()

    return last_value


def is_running(instrument_id):
    logger = logging.getLogger(LOGNAME)

    """
    Returns a string with the running status for a given instrument

    :param instrument_id: Instrument object
    """
    try:
        if not ActiveInstrument.objects.is_adara(instrument_id):
            return "-"
    except:  # noqa: E722
        logger.error("Could not determine whether %s is running ADARA", str(instrument_id))
    try:
        is_recording = False
        key_id = Parameter.objects.get(name="recording")
        last_value = get_latest(instrument_id, key_id)
        if last_value is not None:
            is_recording = last_value.value.lower() == "true"

        is_paused = False
        try:
            key_id = Parameter.objects.get(name="paused")
            last_value = get_latest(instrument_id, key_id)
            if last_value is not None:
                is_paused = last_value.value.lower() == "true"
        except Parameter.DoesNotExist:
            # If we have no pause parameter, it's because the
            # system hasn't paused yet. Treat this as a false.
            # pylint: disable=pointless-except
            pass

        if is_recording:
            if is_paused:
                return "Paused"
            else:
                return "Recording"
        else:
            return "Stopped"
    except:  # noqa: E722
        logger.exception("Could not determine running condition:")
    return "Unknown"


def get_system_health(instrument_id=None):
    """
    Get system health status.
    If an instrument_id is provided, the sub-systems relevant to that instrument will
    also be provided, otherwise only common sub-systems are provided.

    :param instrument_id: Instrument object
    """
    das_status = report_view_util.get_post_processing_status()
    das_status["workflow"] = get_workflow_status()
    if instrument_id is not None:
        das_status["dasmon"] = get_component_status(instrument_id, process="dasmon")
        das_status["pvstreamer"] = get_pvstreamer_status(instrument_id)
    return das_status


def fill_template_values(request, **template_args):
    """
    Fill a template dictionary with information about the instrument
    """
    if "instrument" not in template_args:
        return template_args

    instr = template_args["instrument"].lower()
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instr)

    # Check whether the user is part of the instrument team
    template_args["is_instrument_staff"] = users_view_util.is_instrument_staff(request, instrument_id)

    # Are we currently running ADARA on this instrument?
    is_adara = ActiveInstrument.objects.is_adara(instrument_id)
    is_alive = ActiveInstrument.objects.is_alive(instrument_id)
    template_args["is_adara"] = is_adara
    template_args["is_alive"] = is_alive
    if template_args["is_instrument_staff"] and is_adara:
        template_args["profile_url"] = reverse("dasmon:notifications")

    # Get live monitoring URLs
    template_args["live_monitor_url"] = reverse("dasmon:live_monitor", args=[instr])
    template_args["live_runs_url"] = reverse("dasmon:live_runs", args=[instr])
    template_args["live_pv_url"] = reverse("pvmon:pv_monitor", args=[instr])
    template_args["legacy_url"] = reverse("dasmon:legacy_monitor", args=[instr])

    # template_args["help_url"] = reverse('dasmon:user_help')

    # The DAS monitor link is filled out by report.view_util but we don't need it here
    template_args["dasmon_url"] = None

    # Get the system health status
    template_args["das_status"] = get_system_health(instrument_id)
    if is_adara:
        # Are we recording or not?
        template_args["recording_status"] = is_running(instrument_id)
        # Look information to pull out
        template_args["run_number"] = _find_value(instrument_id, "run_number")
        template_args["count_rate"] = _find_value(instrument_id, "count_rate")
        template_args["proposal_id"] = _find_value(instrument_id, "proposal_id")
        template_args["run_title"] = _find_value(instrument_id, "run_title", "", prune=True)

    return template_args


def _find_value(instrument_id, dasmon_name, default="-", prune=False):
    """
    Return the latest value for a given DASMON entry.

    :param instrument_id: Instrument object
    :param dasmon_name: name of the DASMON entry
    :param default: value to return if no entry is found
    :param prune: if True, title strings will be tidied up
    """
    _value = default
    try:
        key_id = Parameter.objects.get(name=dasmon_name)
        last_value = get_latest(instrument_id, key_id)
        _value = last_value.value
        if prune:
            _value = _prune_title_string(_value)
    except:  # noqa: E722
        # pylint: disable=pointless-except
        pass
    return _value


def get_live_variables(request, instrument_id):
    """
    Create a data dictionary with requested live data

    :param request: HttpRequest object
    :param instrument_id: Instrument object
    """
    logger = logging.getLogger(LOGNAME)
    # Get variable update request
    live_vars = request.GET.get("vars", "")
    if len(live_vars) > 0:
        live_keys = live_vars.split(",")
    else:
        return []
    plot_timeframe = request.GET.get("time", settings.DASMON_PLOT_TIME_RANGE)
    try:
        plot_timeframe = int(plot_timeframe)
    except:  # noqa: E722
        logger.warning("Bad time period request: %s", str(plot_timeframe))
        plot_timeframe = settings.DASMON_PLOT_TIME_RANGE

    data_dict = []
    now = timezone.now()
    two_hours = now - datetime.timedelta(seconds=plot_timeframe)
    for key in live_keys:
        key = key.strip()
        if len(key) == 0:
            continue
        try:
            data_list = []
            key_id = Parameter.objects.get(name=key)
            values = StatusVariable.objects.filter(
                instrument_id=instrument_id, key_id=key_id, timestamp__gte=two_hours
            )
            if len(values) > 0:
                values = values.order_by(settings.DASMON_SQL_SORT).reverse()
            # If you don't have any values for the past 2 hours, just show
            # the latest values up to 20
            if len(values) == 0:
                values = StatusVariable.objects.filter(instrument_id=instrument_id, key_id=key_id)
                if len(values) > 0:
                    values = values.order_by(settings.DASMON_SQL_SORT).reverse()
                else:
                    data_dict.append([key, []])
                    continue
                if len(values) > settings.DASMON_NUMBER_OF_OLD_PTS:
                    values = values[: settings.DASMON_NUMBER_OF_OLD_PTS]

            for v in values:
                delta_t = now - v.timestamp
                data_list.append([-delta_t.total_seconds() / 60.0, float(v.value)])
            data_dict.append([key, data_list])
        except:  # noqa: E722
            # Could not find data for this key
            logger.warning("Could not process %s", key, exc_info=True)
    return data_dict


def get_pvstreamer_status(instrument_id, red_timeout=1, yellow_timeout=None):
    """
    Get the health status of PVStreamer

    :param red_timeout: number of hours before declaring a process dead
    :param yellow_timeout: number of seconds before declaring a process slow
    """
    pvsd_status = -1
    pvstreamer_status = -1
    if ActiveInstrument.objects.has_pvsd(instrument_id):
        pvsd_status = get_component_status(instrument_id, red_timeout, yellow_timeout, process="pvsd")
    if ActiveInstrument.objects.has_pvstreamer(instrument_id):
        pvstreamer_status = get_component_status(instrument_id, red_timeout, yellow_timeout, process="pvstreamer")
    return max(pvstreamer_status, pvsd_status)


def get_component_status(instrument_id, red_timeout=1, yellow_timeout=None, process="dasmon"):
    """
    Get the health status of an ADARA component

    :param red_timeout: number of hours before declaring a process dead
    :param yellow_timeout: number of seconds before declaring a process slow
    """
    logger = logging.getLogger(LOGNAME)
    if yellow_timeout is None:
        yellow_timeout = settings.HEARTBEAT_TIMEOUT
    delta_short = datetime.timedelta(seconds=yellow_timeout)
    delta_long = datetime.timedelta(hours=red_timeout)

    try:
        if not ActiveInstrument.objects.is_adara(instrument_id):
            return -1

        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX + process)
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest("timestamp")
        # Check the status value
        #    STATUS_OK = 0
        #    STATUS_FAULT = 1
        #    STATUS_UNRESPONSIVE = 2
        #    STATUS_INACTIVE = 3
        meaning = {0: "OK", 1: "FAULT", 2: "UNRESPONSIVE", 3: "INACTIVE"}
        if int(last_value.value) > 0:
            value = int(last_value.value)
            logger.error("%s - %s status = %s (%d)", instrument_id, process, meaning.get(value, "UNKNOWN"), value)
            return 2
    except:  # noqa: E722
        logger.debug("No cached status for %s on instrument %s", process, instrument_id.name)
        return 2

    if timezone.now() - last_value.timestamp > delta_long:
        logger.debug("%s has a long delay in %s", process, instrument_id)
        return 2
    elif timezone.now() - last_value.timestamp > delta_short:
        logger.debug("%s has a short delay in %s", process, instrument_id)
        return 1
    return 0


def get_workflow_status(red_timeout=1, yellow_timeout=None):
    """
    Get the health status of Workflow Manager

    :param red_timeout: number of hours before declaring a process dead
    :param yellow_timeout: number of seconds before declaring a process slow
    """
    logger = logging.getLogger(LOGNAME)
    if yellow_timeout is None:
        yellow_timeout = settings.HEARTBEAT_TIMEOUT
    delta_short = datetime.timedelta(seconds=yellow_timeout)
    delta_long = datetime.timedelta(hours=red_timeout)

    try:
        common_services = Instrument.objects.get(name="common")
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX + "workflowmgr")
        last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=key_id).latest("timestamp")
        if int(last_value.value) > 0:
            logger.error("WorkflowMgr status = %s", last_value.value)
            return 2
    except:  # noqa: E722
        logger.debug("No cached status for WorkflowMgr on instrument")
        return 2

    if timezone.now() - last_value.timestamp > delta_long:
        return 2
    elif timezone.now() - last_value.timestamp > delta_short:
        return 1
    return 0


def workflow_diagnostics(timeout=None):
    """
    Diagnostics for the workflow manager

    :param timeout: number of seconds of silence before declaring a problem
    """
    logger = logging.getLogger(LOGNAME)
    if timeout is None:
        timeout = settings.HEARTBEAT_TIMEOUT
    delay_time = datetime.timedelta(seconds=timeout)

    wf_diag = {}
    wf_conditions = []
    dasmon_listener_warning = False

    # Recent reported status
    status_value = -1
    status_time = datetime.datetime(2000, 1, 1, 0, 1).replace(tzinfo=timezone.get_current_timezone())
    common_services = None
    try:
        common_services = Instrument.objects.get(name="common")
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX + "workflowmgr")
        last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=key_id).latest("timestamp")
        status_value = int(last_value.value)
        try:
            status_time = timezone.localtime(last_value.timestamp)
        except:  # noqa: E722
            status_time = last_value.timestamp
    except:  # noqa: E722
        # No data available, keep defaults
        if common_services is None:
            logger.error("workflow_diagnostics could not get 'common' instrument")

    # Determine the number of workflow manager processes running
    process_list = []
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX + "workflowmgr_pid")
        last_values = StatusVariable.objects.filter(instrument_id=common_services, key_id=key_id).order_by(
            "-timestamp"
        )
        pid_list = []
        for item in last_values:
            if item.value not in pid_list:
                pid_list.append(item.value)
                process_list.append({"pid": item.value, "time": timezone.localtime(item.timestamp)})
    except:  # noqa: E722
        logger.exception("workflow_diagnostics:")

    dasmon_listener_list = []
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX + "dasmon_listener_pid")
        last_values = StatusVariable.objects.filter(instrument_id=common_services, key_id=key_id).order_by(
            "-timestamp"
        )
        pid_list = []
        for item in last_values:
            if item.value not in pid_list:
                pid_list.append(item.value)

                dasmon_listener_list.append({"pid": item.value, "time": timezone.localtime(item.timestamp)})
    except:  # noqa: E722
        logger.exception("workflow_diagnostics:")

    # Heartbeat
    # NOTE:
    #   The time entry inside db might or might not have the time zone info.
    #   This try-except block is trying to bypassing it, but it might lead to
    #   some unexpected errors when the time is recorded inconsistently.
    try:
        time_diff = timezone.now() - status_time
    except:  # noqa: E722
        time_diff = timezone.now() - status_time.replace(tzinfo=None)
    if time_diff > delay_time:
        dasmon_listener_warning = True

        wf_conditions.append(
            "No heartbeat since %s: %s"
            % (
                formats.localize(status_time),
                _red_message("contact the Neutron Data Sciences Group or Linux Support"),
            )
        )

    # Status
    if status_value > 0:
        labels = ["OK", "Fault", "Unresponsive", "Inactive"]
        wf_conditions.append("WorkflowMgr reports a status of %s [%s]" % (status_value, labels[status_value]))

    if status_value < 0:
        wf_conditions.append("The web monitor has not heard from WorkflowMgr in a long time: no data available")

    wf_diag["status"] = status_value
    wf_diag["status_time"] = status_time
    wf_diag["conditions"] = wf_conditions
    wf_diag["dasmon_listener_warning"] = dasmon_listener_warning
    wf_diag["processes"] = process_list
    wf_diag["dasmon_listener"] = dasmon_listener_list

    return wf_diag


def postprocessing_diagnostics(timeout=None):
    """
    Diagnostics for the auto-reduction and cataloging

    :param timeout: number of seconds of silence before declaring a problem
    """
    if timeout is None:
        timeout = settings.HEARTBEAT_TIMEOUT

    red_diag = {}
    red_conditions = []

    # Get the status of auto-reduction nodes
    try:
        common_services = Instrument.objects.get(name="common")
        nodes = []
        for item in Parameter.objects.all().order_by("name"):
            for node_prefix in settings.POSTPROCESS_NODE_PREFIX:
                if item.name.startswith(settings.SYSTEM_STATUS_PREFIX + node_prefix):
                    try:
                        if item.name.endswith("_pid"):
                            last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=item).latest(
                                "timestamp"
                            )
                            nodes.append(
                                {
                                    "node": item.name[
                                        len(settings.SYSTEM_STATUS_PREFIX) : len(item.name) - 4  # noqa E203
                                    ],
                                    "time": timezone.localtime(last_value.timestamp),
                                    "msg": f"PID: {last_value.value}",
                                }
                            )
                        else:
                            node = item.name[len(settings.SYSTEM_STATUS_PREFIX) :]  # noqa E203
                            last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=item).latest(
                                "timestamp"
                            )
                            nodes.append(
                                {
                                    "node": node,
                                    "time": timezone.localtime(last_value.timestamp),
                                }
                            )

                            # get last run status performed from Information table by matching node name to description
                            try:
                                last_status = Information.objects.filter(description=node).latest("id")
                                nodes.append(
                                    {
                                        "node": node,  # noqa E203
                                        "time": timezone.localtime(last_status.run_status_id.created_on),
                                        "msg": f"Last msg: {last_status.run_status_id}",
                                    }
                                )
                            except:
                                pass
                    except:  # noqa: E722
                        nodes.append(
                            {
                                "node": item.name[len(settings.SYSTEM_STATUS_PREFIX) :],  # noqa: E203  # noqa E203
                                "time": "No heartbeat - contact the Neutron Data Sciences Group",
                            }
                        )
        red_diag["ar_nodes"] = nodes
    except:  # noqa: E722
        # No data available
        pass

    post_processing = report_view_util.get_post_processing_status()
    if post_processing["catalog"] == 1:
        red_conditions.append("The cataloging was slow in responding to latest requests")
    elif post_processing["catalog"] > 1:
        red_conditions.append(
            "The cataloging is not processing files: %s" % _red_message("contact the Neutron Data Sciences Group")
        )
    if post_processing["reduction"] == 1:
        red_conditions.append("The reduction was slow in responding to latest requests")
    elif post_processing["reduction"] > 1:
        red_conditions.append(
            "The reduction is not processing files: %s" % _red_message("contact the Neutron Data Sciences Group")
        )

    red_diag["catalog_status"] = post_processing["catalog"]
    red_diag["reduction_status"] = post_processing["reduction"]
    red_diag["conditions"] = red_conditions

    return red_diag


def pvstreamer_diagnostics(instrument_id, timeout=None, process="pvstreamer"):
    """
    Diagnostics for PVStreamer

    :param instrument_id: Instrument object
    :param timeout: number of seconds of silence before declaring a problem
    :param process: name of the process to diagnose (pvsd or pvstreamer)
    """
    logger = logging.getLogger(LOGNAME)
    if timeout is None:
        timeout = settings.HEARTBEAT_TIMEOUT
    delay_time = datetime.timedelta(seconds=timeout)

    pv_diag = {}
    pv_conditions = []
    dasmon_listener_warning = False

    # Recent PVStreamer reported status
    status_value = -1
    status_time = datetime.datetime(2000, 1, 1, 0, 1).replace(tzinfo=timezone.get_current_timezone())
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX + process)
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest("timestamp")
        status_value = int(last_value.value)
        try:
            status_time = timezone.localtime(last_value.timestamp)
        except:  # noqa: E722
            status_time = last_value.timestamp
    except:  # noqa: E722
        # No data available, keep defaults
        logger.exception("pvstreamer_diagnostics:")

    # Heartbeat
    try:
        timediff = timezone.now() - status_time
    except:  # noqa: E722
        timediff = timezone.now() - status_time.replace(tzinfo=None)
    if timediff > delay_time:
        dasmon_listener_warning = True
        pv_conditions.append(
            "No %s heartbeat since %s: %s"
            % (
                process,
                formats.localize(status_time),
                _red_message("ask Linux Support or DAS to restart pvsd"),
            )
        )

    # Status
    if status_value > 0:
        labels = ["OK", "Fault", "Unresponsive", "Inactive"]
        pv_conditions.append("%s reports a status of %s [%s]" % (process, status_value, labels[status_value]))

    if status_value < 0:
        pv_conditions.append("The web monitor has not heard from %s in a long time: no data available" % process)

    pv_diag["status"] = status_value
    pv_diag["status_time"] = status_time
    pv_diag["conditions"] = pv_conditions
    pv_diag["dasmon_listener_warning"] = dasmon_listener_warning

    return pv_diag


def dasmon_diagnostics(instrument_id, timeout=None):
    """
    Diagnostics for DASMON

    :param instrument_id: Instrument object
    :param timeout: number of seconds of silence before declaring a problem
    """
    logger = logging.getLogger(LOGNAME)
    if timeout is None:
        timeout = settings.HEARTBEAT_TIMEOUT
    delay_time = datetime.timedelta(seconds=timeout)
    dasmon_diag = {}
    # Recent reported status
    status_value = -1
    status_time = datetime.datetime(2000, 1, 1, 0, 1).replace(tzinfo=timezone.get_current_timezone())
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX + "dasmon")
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest("timestamp")
        status_value = int(last_value.value)
        try:
            status_time = timezone.localtime(last_value.timestamp)
        except:  # noqa: E722
            status_time = last_value.timestamp
    except:  # noqa: E722
        # No data available, keep defaults
        logger.exception("dasmon_diagnostics:")

    # Recent PVs, which come from DASMON straight to the DB
    last_pv_time = datetime.datetime(2000, 1, 1, 0, 1).replace(tzinfo=timezone.get_current_timezone())
    last_pv_timestamp = 0
    try:
        latest = PVCache.objects.filter(instrument=instrument_id).latest("update_time")
        last_pv_time = datetime.datetime.fromtimestamp(latest.update_time).replace(
            tzinfo=timezone.get_current_timezone()
        )
        last_pv_timestamp = latest.update_time
    except:  # noqa: E722
        # No data available, keep defaults
        logger.exception("dasmon_diagnostics:")

    # Recent AMQ messages
    last_amq_time = datetime.datetime(2000, 1, 1, 0, 1).replace(tzinfo=timezone.get_current_timezone())
    try:
        latest = StatusCache.objects.filter(instrument_id=instrument_id).latest("timestamp")
        try:
            last_amq_time = timezone.localtime(latest.timestamp)
        except:  # noqa: E722
            last_amq_time = latest.timestamp
    except:  # noqa: E722
        # No data available, keep defaults
        # pylint: disable=pointless-except
        pass

    # Conditions
    dasmon_conditions = []
    slow_status = False
    slow_pvs = False
    slow_amq = False
    dasmon_listener_warning = False

    # Recent PVs
    if time.time() - last_pv_timestamp > timeout:
        slow_pvs = True
        dasmon_conditions.append("No PV updates in the past %.2f seconds" % float(time.time() - last_pv_timestamp))

    # Recent AMQ
    try:
        dt = timezone.now() - last_amq_time
    except:  # noqa: E722
        dt = timezone.now().replace(tzinfo=None) - last_amq_time.replace(tzinfo=None)
    if dt > delay_time:
        slow_amq = True
        dasmon_conditions.append("No ActiveMQ updates from DASMON since %s" % formats.localize(last_amq_time))

    # Heartbeat
    try:
        dt = timezone.now() - status_time
    except:  # noqa: E722
        dt = timezone.now().replace(tzinfo=None) - status_time.replace(tzinfo=None)
    if dt > delay_time:
        slow_status = True
        dasmon_conditions.append(
            "No heartbeat since %s: %s"
            % (
                formats.localize(status_time),
                _red_message("ask Linux Support or DAS to restart DASMON"),
            )
        )

    # Status
    if status_value > 0:
        labels = ["OK", "Fault", "Unresponsive", "Inactive"]
        dasmon_conditions.append("DASMON reports a status of %s [%s]" % (status_value, labels[status_value]))

    if status_value < 0:
        dasmon_conditions.append("The web monitor has not heard from DASMON in a long time: no data available")

    if slow_status and slow_pvs and slow_amq:
        dasmon_conditions.append(
            "DASMON may be down:  %s" % _red_message("ask Linux Support or DAS to restart DASMON")
        )

    if slow_pvs and not slow_status and not slow_amq:
        dasmon_conditions.append("DASMON is up but not writing to the DB: check pvsd")

    if (slow_status or slow_amq) and not slow_pvs:
        dasmon_conditions.append(
            "DASMON is up and is writing to the DB, but not communicating through AMQ: %s"
            % _red_message("ask Linux Support or DAS to restart DASMON")
        )

    if slow_status and slow_amq:
        dasmon_listener_warning = True

    dasmon_diag["status"] = status_value
    dasmon_diag["status_time"] = status_time
    dasmon_diag["pv_time"] = last_pv_time
    dasmon_diag["amq_time"] = last_amq_time
    dasmon_diag["conditions"] = dasmon_conditions
    dasmon_diag["dasmon_listener_warning"] = dasmon_listener_warning

    return dasmon_diag


def _red_message(msg):
    return "<span class='red'><b>%s</b></span>" % str(msg)


def get_completeness_status(instrument_id):
    """
    Check that the latest runs have successfully completed post-processing

    :param instrument_id: Instrument object
    """
    logger = logging.getLogger(LOGNAME)
    STATUS_OK = (0, "OK")
    # Warning status still says OK but the background color is yellow
    STATUS_WARNING = (1, "OK")
    # Since incomplete might mean error conditions or a simple backlog
    # of runs to process, we report 'incomplete' on a red background
    STATUS_ERROR = (2, "Error")
    STATUS_UNKNOWN = (-1, "Unknown")

    try:
        # Check for completeness of the three runs before the last run.
        # We don't use the last one because we may still be working on it.
        latest_run_id = DataRun.objects.get_last_cached_run(instrument_id)

        # If we don't have any run yet, return unknown
        if latest_run_id is None:
            return STATUS_UNKNOWN

        latest_runs = (
            DataRun.objects.filter(
                instrument_id=instrument_id,
                run_number__gte=latest_run_id.run_number - 3,
            )
            .order_by("created_on")
            .reverse()
        )

        # We need at least 3 runs for a meaningful status
        if len(latest_runs) == 0:
            return STATUS_UNKNOWN
        if len(latest_runs) < 2:
            if WorkflowSummary.objects.get(run_id=latest_runs[0]).complete is True:
                return STATUS_OK
            else:
                return STATUS_WARNING

        r0 = latest_runs[0]
        r1 = latest_runs[1]
        s0 = WorkflowSummary.objects.get(run_id=r0)
        s1 = WorkflowSummary.objects.get(run_id=r1)
        status0 = s0.complete
        status1 = s1.complete
        error0 = r0.last_error() is not None
        error1 = r1.last_error() is not None

        # If the last run is complete, but any of the previous two has an error,
        # then return a warning
        if status0 and (not status1 and error1):
            return STATUS_WARNING

        # If we have errors within the last 3 runs, report an error
        if (not status0 and error0) or (not status1 and error1):
            return STATUS_ERROR

        # If everything but the last run is incomplete, we are OK
        if status1:
            return STATUS_OK

        return STATUS_WARNING
    except:  # noqa: E722
        logger.exception("Output data completeness status")
        return STATUS_UNKNOWN


def get_live_runs_update(request, instrument_id, ipts_id, **data_dict):
    """
    Get updated information about the latest runs

    :param request: HTTP request so we can get the 'since' parameter
    :param instrument_id: Instrument model object
    :param ipts_id: filter by experiment, if provided
    :param data_dict: dictionary to populate
    """
    logger = logging.getLogger(LOGNAME)
    # Get the last run ID that the client knows about
    since_run_id = None
    run_list = []

    if "since" in request.GET and "complete_since" in request.GET:
        since = request.GET.get("since", "0")
        try:
            since = int(since)
            since_run_id = get_object_or_404(DataRun, id=since)
        except:  # noqa: E722
            since = 0

        # Get the earliest run that the client knows about
        complete_since = request.GET.get("complete_since", since)
        try:
            complete_since = int(complete_since)
            # Get last experiment and last run
            if ipts_id is not None:
                run_list = (
                    DataRun.objects.filter(
                        instrument_id=instrument_id,
                        ipts_id=ipts_id,
                        id__gte=complete_since,
                    )
                    .order_by("created_on")
                    .reverse()
                )
            elif instrument_id is not None:
                run_list = (
                    DataRun.objects.filter(instrument_id=instrument_id, id__gte=complete_since)
                    .order_by("created_on")
                    .reverse()
                )
            else:
                run_list = DataRun.objects.filter(id__gte=complete_since).order_by("created_on").reverse()
        except:  # noqa: E722
            # Invalid value for complete_since
            logger.exception("get_live_runs_update:")

    status_list = []
    update_list = []
    if since_run_id is not None and len(run_list) > 0:
        data_dict["last_run_id"] = run_list[0].id
        for r in run_list:
            status = report_view_util.get_run_status_text(r)

            run_dict = {
                "key": "run_id_%s" % str(r.id),
                "value": status,
            }
            status_list.append(run_dict)

            if since_run_id.created_on < r.created_on:
                try:
                    localtime = timezone.localtime(r.created_on)
                except:  # noqa: E722
                    localtime = r.created_on
                reduce_url = reverse(
                    "report:submit_for_reduction",
                    args=[str(r.instrument_id), r.run_number],
                )
                expt_dict = {
                    "run": r.run_number,
                    "timestamp": formats.localize(localtime),
                    "last_error": status,
                    "run_id": r.id,
                    "reduce_url": ("<a id='reduce_%s' href='javascript:void(0);'" % r.run_number)
                    + (' onClick=\'$.ajax({ url: "%s", cache: false });' % reduce_url)
                    + (' $("#reduce_%s").remove();\'>reduce</a>' % r.run_number),  # noqa: E501
                    "instrument_id": str(r.instrument_id),
                }
                update_list.append(expt_dict)
    data_dict["run_list"] = update_list
    data_dict["refresh_needed"] = "1" if len(update_list) > 0 else "0"
    data_dict["status_list"] = status_list
    return data_dict


def get_live_runs(timeframe=12, number_of_entries=25, instrument_id=None, as_html=True):
    """
    Get recent runs for all instruments.
    If no run is found in the last few hours (defined by the timeframe parameter),
    we return the last few runs (defined by the number_of_entries parameter).

    :param timeframe: number of hours going back from now, defining the period of time for the runs
    :param number_of_entries: number of entries to return if we didn't find any run in the defined period
    :param instrument_id: if provided, results will be limited to the given instrument
    """
    logger = logging.getLogger(LOGNAME)
    run_list = []
    first_run = 0
    last_run = 0
    try:
        delta_time = datetime.timedelta(hours=timeframe)
        oldest_time = timezone.now() - delta_time
        if instrument_id is not None:
            runs = (
                DataRun.objects.filter(instrument_id=instrument_id, created_on__gte=oldest_time)
                .order_by("created_on")
                .reverse()
            )
        else:
            runs = DataRun.objects.filter(created_on__gte=oldest_time).order_by("created_on").reverse()
        if len(runs) == 0:
            if instrument_id is not None:
                runs = (
                    DataRun.objects.filter(instrument_id=instrument_id)
                    .order_by("created_on")
                    .reverse()[:number_of_entries]
                )
            else:
                runs = DataRun.objects.order_by("created_on").reverse()[:number_of_entries]
        if len(runs) > 0:
            first_run = runs[len(runs) - 1].id
            last_run = runs[0].id

        # Create dictionary for each run
        if as_html:
            run_list = report_view_util.get_run_list_dict(runs)
        else:
            run_list = get_run_list(runs)
    except:  # noqa: E722
        logger.exception("get_live_runs:")
    return run_list, first_run, last_run


def get_run_list(run_list):
    """
    Get a list of run object and transform it into a list of
    dictionaries that can be used as a simple dictionary that
    can be shipped as json.

    :param run_list: list of run object (usually a QuerySet)
    """
    logger = logging.getLogger(LOGNAME)
    run_dicts = []
    try:
        for r in run_list:
            s = WorkflowSummary.objects.get(run_id=r)
            status = "incomplete"
            if s.complete is True:
                status = "complete"
            elif r.last_error() is not None:
                status = "error"
            # workaround for timezone issue
            try:
                _t = timezone.localtime(r.created_on).ctime()
            except:  # noqa: E722
                _t = r.created_on.ctime()
            run_dicts.append(dict(run=r.run_number, timestamp=_t, status=status))
    except:  # noqa: E722
        logger.exception("dasmon.view_util.get_run_list:")
    return run_dicts


class SignalEntry:
    """
    Utility class representing a DASMON signal
    """

    def __init__(self, name="", status="", assert_time="", key="", ack_url=""):
        self.name = name
        self.status = status
        self.assert_time = assert_time
        self.key = key
        self.ack_url = ack_url
        self.data = None


def get_signals(instrument_id):
    """
    Get the current list of signals/alarms for a given instrument

    :param instrument_id: Instrument object
    """
    logger = logging.getLogger(LOGNAME)
    try:
        signals = Signal.objects.filter(instrument_id=instrument_id)
    except:  # noqa: E722
        logger.exception("Error reading signals:")
        return []

    sig_alerts = []
    for sig in signals:
        sig_entry = SignalEntry(
            name=sig.name,
            status="<span class='red'><b>%s</b></span>" % sig.message,
            assert_time=sig.timestamp,
            ack_url=reverse("dasmon:acknowledge_signal", args=[instrument_id, sig.id]),
        )
        try:
            monitored = MonitoredVariable.objects.filter(instrument=instrument_id, rule_name=sig.name)
            if len(monitored) > 0:
                sig_entry.key = str(monitored[0].pv_name)
        except:  # noqa: E722
            # Could not find an entry for this signal
            logger.exception("Problem finding PV for signal:")

        sig_alerts.append(sig_entry)

    # Get the monitored PVs and signal equivalences
    try:
        monitored = MonitoredVariable.objects.filter(instrument=instrument_id)
        for item in monitored:
            try:
                latests = PVCache.objects.filter(instrument=instrument_id, name=item.pv_name)
                if len(latests) == 0:
                    latests = PVStringCache.objects.filter(instrument=instrument_id, name=item.pv_name)
                latest = latests.latest("update_time")
                if isinstance(latest.value, float):
                    value = "%g" % latest.value
                else:
                    value = "%s" % latest.value
                localtime = datetime.datetime.fromtimestamp(latest.update_time).replace(tzinfo=timezone.utc)
                timestamp = formats.localize(localtime)
            except:  # noqa: E722
                value = "No data available"
                timestamp = "-"
            sig_entry = SignalEntry(name=item.pv_name, status=value, key=item.pv_name, assert_time=timestamp)
            data = pvmon_view_util.get_live_variables(request=None, instrument_id=instrument_id, key_id=item.pv_name)
            data_list = []
            try:
                for point in data[0][1]:
                    data_list.append("%g:%g" % (point[0], point[1]))
            except:  # noqa: E722
                logger.exception()
            sig_entry.data = ",".join(data_list)
            sig_alerts.append(sig_entry)
    except:  # noqa: E722
        logger.exception("Could not process monitored PVs:")

    try:
        return sorted(sig_alerts, key=lambda s: str(s.name).lower())
    except:  # noqa: E722
        logger.exception("Could not sort monitored PV list:")
    return sig_alerts


def get_instrument_status_summary() -> list:
    r"""Status for each instrument in the database,
    used to fill out the summary page template or the summary update response.

    Returns
    -------
    list: List of dictionaries, each representing the status of an instrument. Each dictionary has the following keys:
    - name: str, instrument name
    - recording_status: bool, True if the instrument is currently recording data
    - url: str, URL to access the instrument's live monitor page
    - diagnostics_url: str, URL to access the instrument's diagnostics page
    - dasmon_status: int, status of the DASMON process (0 = OK, 1 = Warning, 2 = Error)
    - pvstreamer_status: int, status of the PVStreamer process (0 = OK, 1 = Warning, 2 = Error)
    - completeness: int, completeness status of the last few runs (0 = OK, 1 = Warning, 2 = Error, -1 = Unknown)
    - completeness_msg: str, message to display for the completeness status
    - facility: str, facility name (default = "SNS
    """
    logger = logging.getLogger(LOGNAME)
    instrument_list = []
    for i in Instrument.objects.all().order_by("name"):
        is_adara = ActiveInstrument.objects.is_adara(i)
        if not ActiveInstrument.objects.is_alive(i):
            continue
        if is_adara:
            dasmon_url = reverse("dasmon:live_monitor", args=[i.name])
            try:
                das_status = get_component_status(i, process="dasmon")
            except:  # noqa: E722
                logger.exception()
                das_status = 2
            try:
                pvstreamer_status = get_pvstreamer_status(i)
            except:  # noqa: E722
                logger.exception()
                pvstreamer_status = 2
        else:
            dasmon_url = reverse("dasmon:live_runs", args=[i.name])
            das_status = -1
            pvstreamer_status = -1
        diagnostics_url = reverse("dasmon:diagnostics", args=[i.name])
        completeness, message = get_completeness_status(i)
        instrument_list.append(
            {
                "name": i.name,
                "recording_status": is_running(i),
                "url": dasmon_url,
                "diagnostics_url": diagnostics_url,
                "dasmon_status": das_status,
                "pvstreamer_status": pvstreamer_status,
                "completeness": completeness,
                "completeness_msg": message,
                "facility": settings.FACILITY_INFO.get(i.name, "SNS"),
            }
        )
    return instrument_list


def get_dashboard_data():
    """
    Get all the run and error rates
    """
    instruments = Instrument.objects.all().order_by("name")
    data_dict = {}
    for i in instruments:
        if not ActiveInstrument.objects.is_alive(i):
            continue
        last_run_id = DataRun.objects.get_last_cached_run(i)
        r_rate, e_rate = report_view_util.retrieve_rates(i, last_run_id)
        data_dict[i.name] = {"run_rate": r_rate, "error_rate": e_rate}
    return data_dict


def add_status_entry(instrument_id, message_channel, value):
    """
    Add a status message for a given instrument.

    :param instrument_id: Instrument object
    :param message_channel: name of the AMQ channel used to report updates
    :param value: value for the entry (string)
    """
    # Find the parameter used to report updates
    try:
        key_id = Parameter.objects.get(name=message_channel)
        update = StatusVariable(instrument_id=instrument_id, key_id=key_id, value=str(value))
        update.save()
    except:  # noqa: E722
        logger = logging.getLogger(LOGNAME)
        logger.error("add_status_entry: could add parameter for %s", message_channel)


def get_latest_updates(instrument_id, message_channel, timeframe=2.0, number_of_entries=10, start_time=None):
    """
    Return a list of recent status messages received on a given channel.

    :param instrument_id: Instrument object
    :param message_channel: name of the AMQ channel used to report updates
    :param timeframe: number of days to report on
    :param number_of_entries: number of recent entries to return if nothing was found in the desired time frame
    :param start_time: earliest time of returned entries. Takes precedence over timeframe and number.
    """
    # Find the parameter used to report updates
    try:
        key_id = Parameter.objects.get(name=message_channel)
    except:  # noqa: E722
        logger = logging.getLogger(LOGNAME)
        logger.error("get_latest_updates: could not find parameter for %s", message_channel)
        return []

    # Determine what's the oldest time stamp we'll report
    if start_time is not None:
        oldest_time = start_time
    else:
        delta_time = datetime.timedelta(days=timeframe)
        oldest_time = timezone.now() - delta_time

    update_list = StatusVariable.objects.filter(instrument_id=instrument_id, key_id=key_id, timestamp__gt=oldest_time)

    # If we don't have any entry in the desired time frame, return the last few
    if len(update_list) > 0:
        update_list = update_list.order_by("timestamp")
    elif start_time is None:
        update_list = (
            StatusVariable.objects.filter(instrument_id=instrument_id, key_id=key_id)
            .order_by("timestamp")
            .reverse()[:number_of_entries]
        )

    template_data = []
    for item in update_list:
        try:
            localtime = timezone.localtime(item.timestamp)
        except:  # noqa: E722
            localtime = item.timestamp
        try:
            ts = timezone.make_naive(item.timestamp, timezone.utc).isoformat()
        except:  # noqa: E722
            ts = item.timestamp.isoformat()
        template_data.append(
            {
                "info": str(item.value),
                "time": formats.localize(localtime),
                "timestamp": ts,
            }
        )
    return template_data


def get_instruments_for_user(request):
    """
    Get the list of instruments for a given user
    """
    # Get the full list of instruments
    instrument_list = []
    for instrument_id in Instrument.objects.all().order_by("name"):
        if not ActiveInstrument.objects.is_alive(instrument_id) or not ActiveInstrument.objects.is_adara(
            instrument_id
        ):
            continue
        instrument_name = str(instrument_id).upper()

        # Django groups
        try:
            gp_name = "%s%s" % (instrument_name, settings.INSTRUMENT_TEAM_SUFFIX)
            instr_group = Group.objects.get(name=gp_name)
            if instr_group in request.user.groups.all():
                instrument_list.append(instrument_name)
                continue
        except Group.DoesNotExist:
            # The group doesn't exist, carry on
            # pylint: disable=pointless-except
            pass

        # LDAP groups
        try:
            if request.user is not None and hasattr(request.user, "ldap_user"):
                groups = request.user.ldap_user.group_names
                if "sns_%s_team" % instrument_name.lower() in groups or "snsadmin" in groups:
                    instrument_list.append(instrument_name)
        except:  # noqa: E722
            # Couldn't find the user in the instrument LDAP group
            # pylint: disable=pointless-except
            pass

    return instrument_list
