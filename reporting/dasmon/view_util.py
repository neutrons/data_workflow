from report.models import Instrument, DataRun, WorkflowSummary, RunStatus, StatusQueue
from dasmon.models import Parameter, StatusVariable, StatusCache, ActiveInstrument, Signal
from pvmon.models import PVName, PV, PVCache, MonitoredVariable
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import dateformat, timezone
import datetime
from django.conf import settings
import logging
import sys
import time
import report.view_util
import pvmon.view_util


def get_cached_variables(instrument_id, monitored_only=False):
    """
        Get cached parameter values for a given instrument
        @param instrument_id: Instrument object
        @param monitored_only: if True, only monitored parameters are returned
    """
    parameter_values = StatusCache.objects.filter(instrument_id=instrument_id).order_by("key_id__name")
    
    key_value_pairs = []
    for kvp in parameter_values:
        if kvp.key_id.monitored or monitored_only is False:
            localtime = timezone.localtime(kvp.timestamp)
            df = dateformat.DateFormat(localtime)
            
            # Check whether we have a number
            try:
                float_value = float(kvp.value)
                string_value = '%g' % float_value
            except:
                string_value = kvp.value
            
            variable_dict = {"key": str(kvp.key_id),
                             "value": string_value,
                             "timestamp": df.format(settings.DATETIME_FORMAT),
                             }
            key_value_pairs.append(variable_dict)    

    return key_value_pairs

def get_latest(instrument_id, key_id):
    """
        Returns the latest entry for a given key on a given instrument
        @param instrument_id: Instrument object
        @param key_id: Parameter object
    """
    # First get it from the cache
    try:
        last_value = StatusCache.objects.filter(instrument_id=instrument_id,
                                                key_id=key_id).latest('timestamp')
    except:
        # If that didn't work, get it from the table of values
        values = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                   key_id=key_id)
        # If we don't have any entry yet, just return Non
        if len(values)==0:
            return None
        last_value = values.latest('timestamp')
        
        # Put the latest value in the cache so we don't have to go through this again
        cached = StatusCache(instrument_id=last_value.instrument_id,
                             key_id=last_value.key_id,
                             value=last_value.value,
                             timestamp=last_value.timestamp)
        cached.save()
        
    return last_value

def is_running(instrument_id):
    """
        Returns a string with the running status for a
        given instrument
        @param instrument_id: Instrument object
    """
    try:
        is_recording = False
        key_id = Parameter.objects.get(name="recording")
        last_value = get_latest(instrument_id, key_id)
        if last_value is not None:
            is_recording = last_value.value.lower()=="true"

        is_paused = False
        try:
            key_id = Parameter.objects.get(name="paused")
            last_value = get_latest(instrument_id, key_id)
            if last_value is not None:
                is_paused = last_value.value.lower()=="true"
        except Parameter.DoesNotExist:
            # If we have no pause parameter, it's because the
            # system hasn't paused yet. Treat this as a false.
            pass
            
        if is_recording:
            if is_paused:
                return "Paused"
            else:
                return "Recording"
        else:
            return "Stopped"
    except:
        logging.error("Could not determine running condition: %s" % sys.exc_value)
    return "Unknown"
    
def get_system_health(instrument_id=None):
    """
        Get system health status.
        If an instrument_id is provided, the sub-systems relevant to that
        instrument will also be provided,
        otherwise only common sub-systems are provided.
        @param instrument_id: Instrument object
    """
    das_status = report.view_util.get_post_processing_status()
    das_status['workflow'] = get_workflow_status()
    if instrument_id is not None:
        das_status['dasmon'] = get_dasmon_status(instrument_id)
        das_status['pvstreamer'] = get_pvstreamer_status(instrument_id)
    return das_status
    
def get_run_status(**template_args):
    """
        Fill a template dictionary with run information
    """
    def _find_and_fill(dasmon_name):
        _value = "Unknown"
        try:
            key_id = Parameter.objects.get(name=dasmon_name)
            last_value = get_latest(instrument_id, key_id)
            _value = last_value.value
        except:
            pass
        template_args[dasmon_name] = _value
    
    if "instrument" not in template_args:
        return template_args
    
    instr = template_args["instrument"].lower()
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instr)
    
    # Look information to pull out
    _find_and_fill("run_number")
    _find_and_fill("count_rate")
    _find_and_fill("proposal_id")
    _find_and_fill("run_title")
    
    # Are we currently running ADARA on this instrument?
    template_args['is_adara'] = ActiveInstrument.objects.is_adara(instrument_id)
    
    # Are we recording or not?
    template_args["recording_status"] = is_running(instrument_id)

    # Get the system health status
    template_args['das_status'] = get_system_health(instrument_id)

    # The DAS monitor link is filled out by report.view_util but we don't need it here
    template_args['dasmon_url'] = None

    # DASMON Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse('dasmon.views.summary'),
            reverse('report.views.instrument_summary',args=[instr]), instr, "monitor"
            ) 
    template_args["breadcrumbs"] = breadcrumbs
    
    template_args["help_url"] = reverse('dasmon.views.help')

    return template_args

def get_live_variables(request, instrument_id):  
    """
        Create a data dictionary with requested live data
    """  
    # Get variable update request
    live_vars = request.GET.get('vars', '')
    if len(live_vars)>0:
        live_keys=live_vars.split(',')
    else:
        return []
    
    data_dict = []
    now = timezone.now()
    two_hours = now-datetime.timedelta(seconds=settings.DASMON_PLOT_TIME_RANGE)
    for key in live_keys:
        key = key.strip()
        if len(key)==0: continue
        try:
            data_list = []
            key_id = Parameter.objects.get(name=key)
            values = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                   key_id=key_id,
                                                   timestamp__gte=two_hours).order_by(settings.DASMON_SQL_SORT).reverse()
            # If you don't have any values for the past 2 hours, just show
            # the latest values up to 20
            if len(values)==0:
                values = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                       key_id=key_id).order_by(settings.DASMON_SQL_SORT).reverse()
                if len(values)>settings.DASMON_NUMBER_OF_OLD_PTS:
                    values = values[:settings.DASMON_NUMBER_OF_OLD_PTS]
            for v in values:
                delta_t = now-v.timestamp
                data_list.append([-delta_t.total_seconds()/60.0, v.value])
            data_dict.append([key,data_list])
        except:
            # Could not find data for this key
            logging.warning("Could not process %s: %s" % (key, sys.exc_value))
    return data_dict

def get_pvstreamer_status(instrument_id, red_timeout=1, yellow_timeout=10):
    """
        Get the health status of PVStreamer
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    delta_short = datetime.timedelta(seconds=yellow_timeout)
    delta_long = datetime.timedelta(hours=red_timeout)
    
    try:
        if not ActiveInstrument.objects.is_adara(instrument_id):
            return -1
    
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'pvstreamer')
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest('timestamp')
        # Check the status value
        #    STATUS_OK = 0
        #    STATUS_FAULT = 1 
        #    STATUS_UNRESPONSIVE = 2
        #    STATUS_INACTIVE = 3
        if int(last_value.value)>0:
            logging.error("PVStreamer status = %s" % last_value.value)
            return 2
    except:
        logging.debug("No cached status for PVStreamer on instrument %s" % instrument_id.name)
        return 2
        
    if timezone.now()-last_value.timestamp>delta_long:
        return 2
    elif timezone.now()-last_value.timestamp>delta_short:
        return 1
    return 0
    
def get_workflow_status(red_timeout=1, yellow_timeout=10):
    """
        Get the health status of Workflow Manager
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    delta_short = datetime.timedelta(seconds=yellow_timeout)
    delta_long = datetime.timedelta(hours=red_timeout)
    
    try:
        common_services = Instrument.objects.get(name='common')
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'workflowmgr')
        last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=key_id).latest('timestamp')
        if int(last_value.value)>0:
            logging.error("WorkflowMgr status = %s" % last_value.value)
            return 2
    except:
        logging.debug("No cached status for WorkflowMgr on instrument")
        return 2
        
    if timezone.now()-last_value.timestamp>delta_long:
        return 2
    elif timezone.now()-last_value.timestamp>delta_short:
        return 1
    return 0
    
def get_dasmon_status(instrument_id, red_timeout=1, yellow_timeout=10):
    """
        Get the health status of DASMON server
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    delta_short = datetime.timedelta(seconds=yellow_timeout)
    delta_long = datetime.timedelta(hours=red_timeout)
    
    try:
        if not ActiveInstrument.objects.is_adara(instrument_id):
            return -1
    
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'dasmon')
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest('timestamp')
        if int(last_value.value)>0:
            logging.error("DASMON status = %s" % last_value.value)
            return 2
    except:
        logging.debug("No cached status for DASMON on instrument %s" % instrument_id.name)
        return 2
        
    if timezone.now()-last_value.timestamp>delta_long:
        return 2
    elif timezone.now()-last_value.timestamp>delta_short:
        return 1
    return 0

def workflow_diagnostics(timeout=10):
    """
        Diagnostics for the workflow manager
        @param timeout: number of seconds of silence before declaring a problem
    """
    delay_time = datetime.timedelta(seconds=timeout)
    
    wf_diag = {}
    wf_conditions = []
    dasmon_listener_warning = False
    
    # Recent reported status
    status_value = -1
    status_time = 0
    try:
        common_services = Instrument.objects.get(name='common')
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'workflowmgr')
        last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=key_id).latest('timestamp')
        status_value = int(last_value.value)
        status_time = timezone.localtime(last_value.timestamp)      
    except:
        # No data available, keep defaults
        pass
    
    # Heartbeat
    if status_time==0 or timezone.now()-status_time>delay_time:
        dasmon_listener_warning = True
        wf_conditions.append("No heartbeat updates for more than %s seconds: %s" % (str(timeout), _red_message("contact Workflow Manager expert")))    

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
    
    return wf_diag
    
def postprocessing_diagnostics(timeout=10):
    """
        Diagnostics for the auto-reduction and cataloging
        @param timeout: number of seconds of silence before declaring a problem
    """
    delay_time = datetime.timedelta(seconds=timeout)

    red_diag = {}
    red_conditions = []

    post_processing = report.view_util.get_post_processing_status()
    if post_processing["catalog"]==1:
        red_conditions.append("The cataloging was slow in responding to latest requests")
    elif post_processing["catalog"]>1:
        red_conditions.append("The cataloging is not processing files: %s" % _red_message("contact Auto Reduction expert"))
    if post_processing["reduction"]==1:
        red_conditions.append("The reduction was slow in responding to latest requests")
    elif post_processing["reduction"]>1:
        red_conditions.append("The reduction is not processing files: %s" % _red_message("contact Auto Reduction expert"))

    red_diag["catalog_status"] = post_processing["catalog"]
    red_diag["reduction_status"] = post_processing["reduction"]
    red_diag["conditions"] = red_conditions
    
    return red_diag


def pvstreamer_diagnostics(instrument_id, timeout=10):
    """
        Diagnostics for PVStreamer
        @param instrument_id: Instrument object
        @param timeout: number of seconds of silence before declaring a problem
    """
    delay_time = datetime.timedelta(seconds=timeout)
    
    pv_diag = {}
    pv_conditions = []
    dasmon_listener_warning = False
    
    # Recent reported status
    status_value = -1
    status_time = 0
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'pvstreamer')
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest('timestamp')
        status_value = int(last_value.value)
        status_time = timezone.localtime(last_value.timestamp)      
    except:
        # No data available, keep defaults
        pass
    
    # Heartbeat
    if status_time==0 or timezone.now()-status_time>delay_time:
        dasmon_listener_warning = True
        pv_conditions.append("No heartbeat updates for more than %s seconds: %s" % (str(timeout), _red_message("contact PVStreamer expert")))

    # Status
    if status_value > 0:
        labels = ["OK", "Fault", "Unresponsive", "Inactive"]
        pv_conditions.append("PVStreamer reports a status of %s [%s]" % (status_value, labels[status_value]))
    
    if status_value < 0:
        pv_conditions.append("The web monitor has not heard from PVStreamer in a long time: no data available")

    pv_diag["status"] = status_value
    pv_diag["status_time"] = status_time
    pv_diag["conditions"] = pv_conditions
    pv_diag["dasmon_listener_warning"] = dasmon_listener_warning
    
    return pv_diag
    
def dasmon_diagnostics(instrument_id, timeout=10):
    """
        Diagnostics for DASMON
        @param instrument_id: Instrument object
        @param timeout: number of seconds of silence before declaring a problem
    """
    delay_time = datetime.timedelta(seconds=timeout)
    dasmon_diag = {}
    # Recent reported status
    status_value = -1
    status_time = 0
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'dasmon')
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest('timestamp')
        status_value = int(last_value.value)
        status_time = timezone.localtime(last_value.timestamp)      
    except:
        # No data available, keep defaults
        pass
    
    # Recent PVs, which come from DASMON straight to the DB
    last_pv_time = 0
    last_pv_timestamp = 0
    try:
        latest = PVCache.objects.filter(instrument=instrument_id).latest("update_time")
        last_pv_time = timezone.localtime(datetime.datetime.fromtimestamp(latest.update_time))
        last_pv_timestamp = latest.update_time
    except:
        # No data available, keep defaults
        pass
    
    # Recent AMQ messages
    last_amq_time = 0
    try:
        latest = StatusCache.objects.filter(instrument_id=instrument_id).latest("timestamp")
        last_amq_time = timezone.localtime(latest.timestamp)
    except:
        # No data available, keep defaults
        pass
    
    # Conditions
    dasmon_conditions = []
    slow_status = False
    slow_pvs = False
    slow_amq = False
    dasmon_listener_warning = False
    
    # Recent PVs
    if last_pv_timestamp==0 or time.time()-last_pv_timestamp>timeout:
        slow_pvs = True
        dasmon_conditions.append("No PV updates in the past %s seconds" % str(timeout))
    
    # Recent AMQ
    if last_amq_time==0 or timezone.now()-last_amq_time>delay_time:
        slow_amq = True
        dasmon_conditions.append("No ActiveMQ updates from DASMON in the past %s seconds" % str(timeout))
    
    # Heartbeat
    if status_time==0 or timezone.now()-status_time>delay_time:
        slow_status = True
        dasmon_conditions.append("No heartbeat updates for more than %s seconds: %s" % (str(timeout), _red_message("contact DASMON expert")))     
    
    # Status
    if status_value > 0:
        labels = ["OK", "Fault", "Unresponsive", "Inactive"]
        dasmon_conditions.append("DASMON reports a status of %s [%s]" % (status_value, labels[status_value]))
    
    if status_value < 0:
        dasmon_conditions.append("The web monitor has not heard from DASMON in a long time: no data available")
    
    if slow_status and slow_pvs and slow_amq:
        dasmon_conditions.append("DASMON may be down:  %s" % _red_message("contact DASMON expert"))
    
    if slow_pvs and not slow_status and not slow_amq:
        dasmon_conditions.append("DASMON is up but not writing to the DB: check PVStreamer")
    
    if (slow_status or slow_amq) and not slow_pvs:
        dasmon_conditions.append("DASMON is up and is writing to the DB, but not communicating through AMQ: %s" % _red_message("contact DASMON expert"))

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
        @param instrument_id: Instrument object
    """
    STATUS_OK = (0, "OK")
    STATUS_WARNING = (1, "Warning")
    STATUS_ERROR = (2, "Error")
    STATUS_UNKNOWN = (-1, "Unknown")

    if not ActiveInstrument.objects.is_alive(instrument_id):
        return (-1, "OK")
    
    try:
        # Check for completeness of the three runs before the last run.
        # We don't use the last one because we may still be working on it.
        latest_runs = DataRun.objects.filter(instrument_id=instrument_id)

        # We need at least 4 runs for a meaningful status        
        if len(latest_runs)==0:    
            return STATUS_UNKNOWN
        if len(latest_runs)<4:
            if WorkflowSummary.objects.get(run_id=latest_runs[0]).complete is True:
                return STATUS_OK
            else:
                return STATUS_WARNING
        
        latest_runs = latest_runs.order_by("created_on").reverse()
        s0 = WorkflowSummary.objects.get(run_id=latest_runs[0])
        s1 = WorkflowSummary.objects.get(run_id=latest_runs[1])
        s2 = WorkflowSummary.objects.get(run_id=latest_runs[2])
        s3 = WorkflowSummary.objects.get(run_id=latest_runs[3])
        # If the latest is complete, use it to determine the status        
        if s0.complete:
            status0 = s0.complete
            status1 = s1.complete
            status2 = s2.complete
        # If the latest is incomplete, it might still be processing, skip it
        else:
            status0 = s1.complete
            status1 = s2.complete
            status2 = s3.complete
        
        # Determine status
        if status0 is False:
            return STATUS_ERROR
        else:
            if status1 is False or status2 is False:
                return STATUS_WARNING
            else:
                return STATUS_OK
    except:
        logging.error("Output data completeness status")
        logging.error(sys.exc_value)
        return STATUS_UNKNOWN

def get_live_runs_update(request, instrument_id):
    """
         Get updated information about the latest runs
         @param request: HTTP request so we can get the 'since' parameter
         @param instrument_id: Instrument model object
    """ 
    data_dict = {}
    
    # Get the last run ID that the client knows about
    since_run_id = None
    run_list = []

    if request.GET.has_key('since') and request.GET.has_key('complete_since'):
        since = request.GET.get('since', '0')
        try:
            since = int(since)
            since_run_id = get_object_or_404(DataRun, id=since)
        except:
            since = 0
        
        # Get the earliest run that the client knows about
        complete_since = request.GET.get('complete_since', since)
        try:
            complete_since = int(complete_since)
            # Get last experiment and last run
            run_list = DataRun.objects.filter(instrument_id=instrument_id, id__gte=complete_since).order_by('created_on').reverse()
        except:
            # Invalid value for complete_since
            pass

    status_list = []
    update_list = []
    if since_run_id is not None and len(run_list)>0:
        data_dict['last_run_id'] = run_list[0].id
        for r in run_list:
            status = 'unknown'
            try:
                s = WorkflowSummary.objects.get(run_id=r)
                if s.complete is True:
                    status = "<span class='green'>complete</span>"
                else:
                    status = "<span class='red'>incomplete</span>"
            except:
                # No entry for this run
                pass
            
            run_dict = {"key": "run_id_%s" % str(r.id),
                        "value": status,
                        }
            status_list.append(run_dict)
            
            if since_run_id.created_on < r.created_on:
                localtime = timezone.localtime(r.created_on)
                df = dateformat.DateFormat(localtime)
                expt_dict = {"run":r.run_number,
                            "timestamp":df.format(settings.DATETIME_FORMAT),
                            "last_error":status,
                            "run_id":str(r.id),
                            }
                update_list.append(expt_dict)
    data_dict['run_list'] = update_list
    data_dict['refresh_needed'] = '1' if len(update_list)>0 else '0'
    data_dict['status_list'] = status_list
    return data_dict


class SignalEntry(object):
    """
        Utility class representing a DASMON signal
    """
    def __init__(self, name='', status='', assert_time='', key=''):
        self.name = name
        self.status = status
        self.assert_time = assert_time
        self.key = key
    
def get_signals(instrument_id):
    """
        Get the current list of signals/alarms for a given instrument
        @param instrument_id: Instrument object 
    """
    try:
        signals = Signal.objects.filter(instrument_id=instrument_id)
    except:
        logging.error("Error reading signals: %s" % sys.exc_value)
        return []
        
    sig_alerts = []
    used_keys = []
    for sig in signals:
        sig_entry = SignalEntry(name=sig.name,
                                status="<span class='red'><b>%s</b></span>" % sig.message,
                                assert_time=sig.timestamp)
        try:
            monitored = MonitoredVariable.objects.filter(instrument=instrument_id,
                                                         rule_name=sig.name)
            if len(monitored)>0:
                sig_entry.key = str(monitored[0].pv_name)
                used_keys.append(sig_entry.key)
        except:
            # Could not find an entry for this signal
            logging.error("Problem finding PV for signal: %s" % sys.exc_value)
            
        sig_alerts.append(sig_entry)
        
    # Get the monitored PVs and signal equivalences
    try:
        monitored = MonitoredVariable.objects.filter(instrument=instrument_id)
        for item in monitored:
            if str(item.pv_name) not in used_keys:
                try:
                    latest = PVCache.objects.filter(instrument=instrument_id, name=item.pv_name).latest("update_time")
                    value = '%g' % latest.value
                    localtime = timezone.localtime(datetime.datetime.fromtimestamp(latest.update_time))
                    df = dateformat.DateFormat(localtime)
                    timestamp = df.format(settings.DATETIME_FORMAT)
                except:
                    value = 'No data available'
                    timestamp = '-'
                sig_entry = SignalEntry(name=item.pv_name, status=value, 
                                        key=item.pv_name, assert_time=timestamp)
                sig_alerts.append(sig_entry)
    except:
        logging.error("Could not process monitored PVs: %s" % sys.exc_value)
        
    return sig_alerts
