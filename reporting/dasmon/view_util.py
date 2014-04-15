"""
    Status monitor utilities to support 'dasmon' views
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from report.models import Instrument, DataRun, WorkflowSummary
from dasmon.models import Parameter, StatusVariable, StatusCache, ActiveInstrument, Signal
from pvmon.models import PVCache, MonitoredVariable
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import dateformat, timezone
import datetime
from django.conf import settings
import logging
import sys
import time
import math
import report.view_util
import pvmon.view_util
import users.view_util

def get_monitor_breadcrumbs(instrument_id, current_view='monitor'):
    """
        Create breadcrumbs for a live monitoring view
        @param instrument_id: Instrument object
        @param current_view: name to give this view
    """
    breadcrumbs = "<a href='%s'>home</a>" % reverse('dasmon.views.summary')
    if ActiveInstrument.objects.is_alive(instrument_id):
        breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (reverse('report.views.instrument_summary',
                                                                 args=[instrument_id.name]),
                                                         instrument_id.name)
    else:
        breadcrumbs += " &rsaquo; %s" % instrument_id.name
    breadcrumbs += " &rsaquo; %s" % current_view
    return breadcrumbs
    
def get_cached_variables(instrument_id, monitored_only=False):
    """
        Get cached parameter values for a given instrument
        @param instrument_id: Instrument object
        @param monitored_only: if True, only monitored parameters are returned
    """
    parameter_values = StatusCache.objects.filter(instrument_id=instrument_id).order_by("key_id__name")
    # Variables that are displayed on top
    top_variables = ['run_number', 'proposal_id', 'run_title']
    key_value_pairs = []
    for kvp in parameter_values:
        if kvp.key_id.monitored or monitored_only is False:
            # Exclude top variables
            if monitored_only and str(kvp.key_id) in top_variables:
                continue
            localtime = timezone.localtime(kvp.timestamp)
            df = dateformat.DateFormat(localtime)
            
            # Check whether we have a number
            try:
                float_value = float(kvp.value)
                string_value = '%g' % float_value
            except:
                string_value = kvp.value
            
            # Tweak the title string so we don't have ><
            if str(kvp.key_id)=='run_title':
                string_value = _prune_title_string(string_value)
                
            variable_dict = {"key": str(kvp.key_id),
                             "value": string_value,
                             "timestamp": df.format(settings.DATETIME_FORMAT),
                             }
            key_value_pairs.append(variable_dict)    

    return key_value_pairs

def _prune_title_string(value):
    """
        Replace unusual characters in a string.
        This is mostly for run titles which come in
        from the DAS with weird delimiters.
        @param value: string
    """
    try:
        pruned = value
        if pruned.endswith('><'):
            pruned = pruned[:len(pruned)-2]
        toks = pruned.split('><')
        if len(toks)>1:
            comments = "<span style='font-size:small'>%s</span>" % "<br>".join(toks[1:])
            return "%s<br>%s" % (toks[0], comments)
        else:
            return pruned
    except:
        return value
   
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
        if not ActiveInstrument.objects.is_adara(instrument_id):
            return '-'
    except:
        logging.error("Could not determine whether %s is running ADARA" % str(instrument_id))
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
    template_args['is_instrument_staff'] = users.view_util.is_instrument_staff(request, instrument_id)

    # Are we currently running ADARA on this instrument?
    is_adara = ActiveInstrument.objects.is_adara(instrument_id)
    is_alive = ActiveInstrument.objects.is_alive(instrument_id)
    template_args['is_adara'] = is_adara
    template_args['is_alive'] = is_alive

    # Get live monitoring URLs
    template_args['live_monitor_url'] = reverse('dasmon.views.live_monitor', args=[instr])
    template_args['live_runs_url'] = reverse('dasmon.views.live_runs', args=[instr])
    template_args['live_pv_url'] = reverse('pvmon.views.pv_monitor', args=[instr])
    template_args['legacy_url'] = reverse('dasmon.views.legacy_monitor', args=[instr])

    #template_args["help_url"] = reverse('dasmon.views.help')

    # The DAS monitor link is filled out by report.view_util but we don't need it here
    template_args['dasmon_url'] = None
    
    # Get the system health status
    template_args['das_status'] = get_system_health(instrument_id)
    if is_adara:
        # Are we recording or not?
        template_args["recording_status"] = is_running(instrument_id)
        # Look information to pull out
        template_args["run_number"] = _find_value(instrument_id, "run_number")
        template_args["count_rate"] = _find_value(instrument_id, "count_rate")
        template_args["proposal_id"] = _find_value(instrument_id, "proposal_id")
        template_args["run_title"] = _find_value(instrument_id, "run_title", '', prune=True)

    return template_args    

def _find_value(instrument_id, dasmon_name, default='-', prune=False):
    """
        Return the latest value for a given DASMON entry.
        @param instrument_id: Instrument object
        @param dasmon_name: name of the DASMON entry
        @param default: value to return if no entry is found
        @param prune: if True, title strings will be tidied up
    """
    _value = default
    try:
        key_id = Parameter.objects.get(name=dasmon_name)
        last_value = get_latest(instrument_id, key_id)
        _value = last_value.value
        if prune:
            _value = _prune_title_string(_value)
    except:
        pass
    return _value

def get_live_variables(request, instrument_id):  
    """
        Create a data dictionary with requested live data
        
        @param request: HttpRequest object
        @param instrument_id: Instrument object
    """  
    # Get variable update request
    live_vars = request.GET.get('vars', '')
    if len(live_vars)>0:
        live_keys=live_vars.split(',')
    else:
        return []
    plot_timeframe = request.GET.get('time', settings.DASMON_PLOT_TIME_RANGE)
    try:
        plot_timeframe = int(plot_timeframe)
    except:
        logging.warning("Bad time period request: %s" % str(plot_timeframe))
        plot_timeframe = settings.DASMON_PLOT_TIME_RANGE
    
    data_dict = []
    now = timezone.now()
    two_hours = now-datetime.timedelta(seconds=plot_timeframe)
    for key in live_keys:
        key = key.strip()
        if len(key)==0: continue
        try:
            data_list = []
            key_id = Parameter.objects.get(name=key)
            values = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                   key_id=key_id,
                                                   timestamp__gte=two_hours)
            if len(values)>0:
                values = values.order_by(settings.DASMON_SQL_SORT).reverse()
            # If you don't have any values for the past 2 hours, just show
            # the latest values up to 20
            if len(values)==0:
                values = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                       key_id=key_id)
                if len(values)>0:
                    values = values.order_by(settings.DASMON_SQL_SORT).reverse()
                else:
                    data_dict.append([key,[]])
                    continue
                if len(values)>settings.DASMON_NUMBER_OF_OLD_PTS:
                    values = values[:settings.DASMON_NUMBER_OF_OLD_PTS]
            
            # Average out points every two minutes when plotting a long period of time
            if now-values[len(values)-1].timestamp>datetime.timedelta(seconds=2*60*60):
                range_t = now-values[len(values)-1].timestamp
                range_minutes = int(math.floor(range_t.total_seconds()/120))+1
                data_values = range_minutes*[0]
                data_counts = range_minutes*[0]
                for v in values:
                    delta_t = now-v.timestamp
                    i_bin = int(math.floor(delta_t.total_seconds()/120))
                    if i_bin<range_minutes:
                        data_counts[i_bin] += 1.0
                        data_values[i_bin] += float(v.value)
                    else:
                        logging.warning("Skipping point %s/%s %s(%s) = %s" % (i_bin, range_minutes, key, v.timestamp, v.value))
                for i in range(range_minutes):
                    if data_counts[i]>0:
                        data_values[i] /= data_counts[i]
                    data_list.append([-i*2.0, data_values[i]])
            else:
                for v in values:
                    delta_t = now-v.timestamp
                    data_list.append([-delta_t.total_seconds()/60.0, v.value])
            data_dict.append([key,data_list])
        except:
            # Could not find data for this key
            logging.warning("Could not process %s: %s" % (key, sys.exc_value))
    return data_dict

def get_pvstreamer_status(instrument_id, red_timeout=1, yellow_timeout=None):
    """
        Get the health status of PVStreamer
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    if yellow_timeout is None:
        yellow_timeout = settings.HEARTBEAT_TIMEOUT
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
    
def get_workflow_status(red_timeout=1, yellow_timeout=None):
    """
        Get the health status of Workflow Manager
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    if yellow_timeout is None:
        yellow_timeout = settings.HEARTBEAT_TIMEOUT
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
    
def get_dasmon_status(instrument_id, red_timeout=1, yellow_timeout=None):
    """
        Get the health status of DASMON server
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    if yellow_timeout is None:
        yellow_timeout = settings.HEARTBEAT_TIMEOUT
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

def workflow_diagnostics(timeout=None):
    """
        Diagnostics for the workflow manager
        @param timeout: number of seconds of silence before declaring a problem
    """
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
        common_services = Instrument.objects.get(name='common')
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'workflowmgr')
        last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=key_id).latest('timestamp')
        status_value = int(last_value.value)
        status_time = timezone.localtime(last_value.timestamp)
    except:
        # No data available, keep defaults
        if common_services is None:
            logging.error("workflow_diagnostics could not get 'common' instrument")
    
    # Determine the number of workflow manager processes running
    process_list = []
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'workflowmgr_pid')
        last_values = StatusVariable.objects.filter(instrument_id=common_services, key_id=key_id).order_by('-timestamp')
        pid_list = []
        for item in last_values:
            if item.value not in pid_list:
                pid_list.append(item.value)
                process_list.append({'pid': item.value,
                                     'time': timezone.localtime(item.timestamp)})
    except:
        logging.error("workflow_diagnostics: %s" % sys.exc_value)
    
    dasmon_listener_list = []
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'dasmon_listener_pid')
        last_values = StatusVariable.objects.filter(instrument_id=common_services, key_id=key_id).order_by('-timestamp')
        pid_list = []
        for item in last_values:
            if item.value not in pid_list:
                pid_list.append(item.value)
                
                dasmon_listener_list.append({'pid': item.value,
                                            'time': timezone.localtime(item.timestamp)})
    except:
        logging.error("workflow_diagnostics: %s" % sys.exc_value)
    
    # Heartbeat
    if timezone.now()-status_time>delay_time:
        dasmon_listener_warning = True
        df = dateformat.DateFormat(status_time)
        wf_conditions.append("No heartbeat since %s: %s" % (df.format(settings.DATETIME_FORMAT), _red_message("contact Workflow Manager expert")))

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
        @param timeout: number of seconds of silence before declaring a problem
    """
    if timeout is None:
        timeout = settings.HEARTBEAT_TIMEOUT
    delay_time = datetime.timedelta(seconds=timeout)

    red_diag = {}
    red_conditions = []

    # Get the status of auto-reduction nodes
    try:
        common_services = Instrument.objects.get(name='common')
        nodes = []
        for item in Parameter.objects.all():
            for node_prefix in settings.POSTPROCESS_NODE_PREFIX:
                if item.name.startswith(settings.SYSTEM_STATUS_PREFIX+node_prefix):
                    try:
                        if item.name.endswith('_pid'):
                            last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=item).latest('timestamp')
                            nodes.append({'node':'%s PID %s' % (item.name[len(settings.SYSTEM_STATUS_PREFIX):len(item.name)-4], last_value.value),
                                          'time':timezone.localtime(last_value.timestamp)})
                        else:
                            last_value = StatusCache.objects.filter(instrument_id=common_services, key_id=item).latest('timestamp')
                            nodes.append({'node':item.name[len(settings.SYSTEM_STATUS_PREFIX):],
                                          'time':timezone.localtime(last_value.timestamp)})
                    except:
                        nodes.append({'node':item.name[len(settings.SYSTEM_STATUS_PREFIX):],
                                      'time':'No heartbeat - contact post-processing expert'})
        red_diag['ar_nodes']=nodes
    except:
        # No data available
        pass

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


def pvstreamer_diagnostics(instrument_id, timeout=None, process='pvstreamer'):
    """
        Diagnostics for PVStreamer
        @param instrument_id: Instrument object
        @param timeout: number of seconds of silence before declaring a problem
        @param process: name of the process to diagnose (pvsd or pvstreamer)
    """
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
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+process)
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest('timestamp')
        status_value = int(last_value.value)
        status_time = timezone.localtime(last_value.timestamp)
    except:
        # No data available, keep defaults
        pass
    
    # Heartbeat
    if timezone.now()-status_time>delay_time:
        dasmon_listener_warning = True
        df = dateformat.DateFormat(status_time)
        pv_conditions.append("No %s heartbeat since %s: %s" % (process, df.format(settings.DATETIME_FORMAT), _red_message("ask on-call instrument contact to restart PVStreamer")))

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
        @param instrument_id: Instrument object
        @param timeout: number of seconds of silence before declaring a problem
    """
    if timeout is None:
        timeout = settings.HEARTBEAT_TIMEOUT
    delay_time = datetime.timedelta(seconds=timeout)
    dasmon_diag = {}
    # Recent reported status
    status_value = -1
    status_time = datetime.datetime(2000, 1, 1, 0, 1).replace(tzinfo=timezone.get_current_timezone())
    try:
        key_id = Parameter.objects.get(name=settings.SYSTEM_STATUS_PREFIX+'dasmon')
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest('timestamp')
        status_value = int(last_value.value)
        status_time = timezone.localtime(last_value.timestamp)      
    except:
        # No data available, keep defaults
        pass
    
    # Recent PVs, which come from DASMON straight to the DB
    last_pv_time = datetime.datetime(2000, 1, 1, 0, 1).replace(tzinfo=timezone.get_current_timezone())
    last_pv_timestamp = 0
    try:
        latest = PVCache.objects.filter(instrument=instrument_id).latest("update_time")
        last_pv_time = timezone.localtime(datetime.datetime.fromtimestamp(latest.update_time))
        last_pv_timestamp = latest.update_time
    except:
        # No data available, keep defaults
        pass
    
    # Recent AMQ messages
    last_amq_time = datetime.datetime(2000, 1, 1, 0, 1).replace(tzinfo=timezone.get_current_timezone())
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
    if time.time()-last_pv_timestamp>timeout:
        slow_pvs = True
        dasmon_conditions.append("No PV updates in the past %s seconds" % str(time.time()-last_pv_timestamp))
    
    # Recent AMQ
    if timezone.now()-last_amq_time>delay_time:
        slow_amq = True
        df = dateformat.DateFormat(last_amq_time)
        dasmon_conditions.append("No ActiveMQ updates from DASMON since %s" % df.format(settings.DATETIME_FORMAT))
    
    # Heartbeat
    if timezone.now()-status_time>delay_time:
        slow_status = True
        df = dateformat.DateFormat(status_time)
        dasmon_conditions.append("No heartbeat since %s: %s" % (df.format(settings.DATETIME_FORMAT), _red_message("ask on-call instrument contact to restart DASMON")))     
    
    # Status
    if status_value > 0:
        labels = ["OK", "Fault", "Unresponsive", "Inactive"]
        dasmon_conditions.append("DASMON reports a status of %s [%s]" % (status_value, labels[status_value]))
    
    if status_value < 0:
        dasmon_conditions.append("The web monitor has not heard from DASMON in a long time: no data available")
    
    if slow_status and slow_pvs and slow_amq:
        dasmon_conditions.append("DASMON may be down:  %s" % _red_message("ask on-call instrument contact to restart DASMON"))
    
    if slow_pvs and not slow_status and not slow_amq:
        dasmon_conditions.append("DASMON is up but not writing to the DB: check PVStreamer")
    
    if (slow_status or slow_amq) and not slow_pvs:
        dasmon_conditions.append("DASMON is up and is writing to the DB, but not communicating through AMQ: %s" % _red_message("ask on-call instrument contact to restart DASMON"))

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
        
        latest_runs = DataRun.objects.filter(instrument_id=instrument_id,
                                             run_number__gte=latest_run_id.run_number-3).order_by("created_on").reverse()

        # We need at least 3 runs for a meaningful status        
        if len(latest_runs)==0:    
            return STATUS_UNKNOWN
        if len(latest_runs)<3:
            if WorkflowSummary.objects.get(run_id=latest_runs[0]).complete is True:
                return STATUS_OK
            else:
                return STATUS_WARNING
        
        r0 = latest_runs[0]
        r1 = latest_runs[1]
        r2 = latest_runs[2]
        s0 = WorkflowSummary.objects.get(run_id=r0)
        s1 = WorkflowSummary.objects.get(run_id=r1)
        s2 = WorkflowSummary.objects.get(run_id=r2)
        status0 = s0.complete
        status1 = s1.complete
        status2 = s2.complete
        error0 = r0.last_error() is not None
        error1 = r1.last_error() is not None
        error2 = r2.last_error() is not None
        
        # If we have errors within the last 3 runs, report an error
        if (not status0 and error0) or (not status1 and error1) or (not status2 and error2):
            return STATUS_ERROR
        
        # If everything but the last run is incomplete, we are OK
        if status1 and status2:
            return STATUS_OK
        
        return STATUS_WARNING
    except:
        logging.error("Output data completeness status")
        logging.error(sys.exc_value)
        return STATUS_UNKNOWN

def get_run_status_text(run_id, show_error=False):
    """
        Get a textual description of the current status
        for a given run
        @param run_id: run object
        @param show_error: if true, the last error will be whow, otherwise "error"
    """
    status = 'unknown'
    try:
        s = WorkflowSummary.objects.get(run_id=run_id)
        if s.complete is True:
            status = "<span class='green'>complete</span>"
        else:
            last_error = run_id.last_error()
            if last_error is not None:
                if show_error:
                    status = "<span class='red'>%s</span>" % last_error
                else:
                    status = "<span class='red'><b>error</b></span>"
            else:
                status = "<span class='red'>incomplete</span>"
    except:
        # No entry for this run
        pass    
    return status

def get_live_runs_update(request, instrument_id, ipts_id, **data_dict):
    """
         Get updated information about the latest runs
         @param request: HTTP request so we can get the 'since' parameter
         @param instrument_id: Instrument model object
         @param ipts_id: filter by experiment, if provided
         @param data_dict: dictionary to populate
    """     
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
            if ipts_id is not None:
                run_list = DataRun.objects.filter(instrument_id=instrument_id,
                                                  ipts_id=ipts_id,
                                                  id__gte=complete_since).order_by('created_on').reverse()
            else:
                run_list = DataRun.objects.filter(instrument_id=instrument_id,
                                                  id__gte=complete_since).order_by('created_on').reverse()
        except:
            # Invalid value for complete_since
            pass

    status_list = []
    update_list = []
    if since_run_id is not None and len(run_list)>0:
        data_dict['last_run_id'] = run_list[0].id
        for r in run_list:
            status = get_run_status_text(r, ipts_id is not None)
            
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
    def __init__(self, name='', status='', assert_time='', key='', ack_url=''):
        self.name = name
        self.status = status
        self.assert_time = assert_time
        self.key = key
        self.ack_url = ack_url
        self.data = None
    
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
    for sig in signals:
        sig_entry = SignalEntry(name=sig.name,
                                status="<span class='red'><b>%s</b></span>" % sig.message,
                                assert_time=sig.timestamp,
                                ack_url=reverse('dasmon.views.acknowledge_signal',args=[instrument_id, sig.id]))
        try:
            monitored = MonitoredVariable.objects.filter(instrument=instrument_id,
                                                         rule_name=sig.name)
            if len(monitored)>0:
                sig_entry.key = str(monitored[0].pv_name)
        except:
            # Could not find an entry for this signal
            logging.error("Problem finding PV for signal: %s" % sys.exc_value)
            
        sig_alerts.append(sig_entry)
        
    # Get the monitored PVs and signal equivalences
    try:
        monitored = MonitoredVariable.objects.filter(instrument=instrument_id)
        for item in monitored:
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
            data = pvmon.view_util.get_live_variables(request=None, 
                                                      instrument_id=instrument_id, 
                                                      key_id=item.pv_name)
            data_list = []
            try:
                for point in data[0][1]:
                    data_list.append('%g:%g' % (point[0], point[1]))
            except:
                logging.error(sys.exc_value)
            sig_entry.data=','.join(data_list)
            sig_alerts.append(sig_entry)
    except:
        logging.error("Could not process monitored PVs: %s" % sys.exc_value)
        
    return sig_alerts

def get_instrument_status_summary():
    """
        Create an instrument status dictionary that can be used
        to fill out the summary page template or the summary update response.
    """
    instrument_list = []
    for i in Instrument.objects.all().order_by('name'):
        is_adara = ActiveInstrument.objects.is_adara(i)
        if not ActiveInstrument.objects.is_alive(i):
            continue
        if is_adara:
            dasmon_url = reverse('dasmon.views.live_monitor',args=[i.name])
            das_status = get_dasmon_status(i)
            pvstreamer_status = get_pvstreamer_status(i)
        else:
            dasmon_url = reverse('dasmon.views.live_runs',args=[i.name])
            das_status = -1
            pvstreamer_status = -1
        diagnostics_url = reverse('dasmon.views.diagnostics', args=[i.name])
        completeness, message = get_completeness_status(i)
        instrument_list.append({'name': i.name,
                                'recording_status': is_running(i),
                                'url': dasmon_url,
                                'diagnostics_url': diagnostics_url,
                                'dasmon_status': das_status,
                                'pvstreamer_status': pvstreamer_status,
                                'completeness': completeness,
                                'completeness_msg': message
                                })
    return instrument_list
    