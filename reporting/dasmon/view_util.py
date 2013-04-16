from report.models import Instrument, DataRun, WorkflowSummary, RunStatus, StatusQueue
from dasmon.models import Parameter, StatusVariable, StatusCache
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import dateformat, timezone
import datetime
from django.conf import settings
import logging
import sys
import report.view_util

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
        last_value = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                   key_id=key_id).latest('timestamp')
        
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
        key_id = Parameter.objects.get(name="recording")
        last_value = get_latest(instrument_id, key_id)
        is_recording = last_value.value.lower()=="true"

        key_id = Parameter.objects.get(name="paused")
        last_value = get_latest(instrument_id, key_id)
        is_paused = last_value.value.lower()=="true"
            
        if is_recording:
            if is_paused:
                return "Paused"
            else:
                return "Recording"
        else:
            return "Stopped"
    except:
        pass
    return "Unknown"
    
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
    
    # Are we recording or not?
    template_args["recording_status"] = is_running(instrument_id)

    # Get the system health status
    das_status = report.view_util.get_post_processing_status()
    das_status['dasmon'] = get_dasmon_status(instrument_id)
    template_args['das_status'] = das_status

    # The DAS monitor link is filled out by report.view_util but we don't need it here
    template_args['dasmon_url'] = None

    # DASMON Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse('dasmon.views.summary'),
            reverse('report.views.instrument_summary',args=[instr]), instr, "DAS monitor"
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
    two_hours = now-datetime.timedelta(hours=2)
    for key in live_keys:
        key = key.strip()
        if len(key)==0: continue
        try:
            data_list = []
            key_id = Parameter.objects.get(name=key)
            values = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                   key_id=key_id,
                                                   timestamp__gte=two_hours)
            # If you don't have any values for the past 2 hours, just show
            # the latest values up to 20
            if len(values)==0:
                values = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                       key_id=key_id).order_by(settings.DASMON_SQL_SORT).reverse()
                if len(values)>20:
                    values = values[:20]
            for v in values:
                delta_t = now-v.timestamp
                data_list.append([-delta_t.seconds/60.0, v.value])
            data_dict.append([key,data_list])
        except:
            # Could not find data for this key
            logging.warning("Could not process %s: %s" % (key, sys.exc_value))
    return data_dict

def get_dasmon_status(instrument_id, red_timeout=1, yellow_timeout=10):
    """
        Get the health status of DASMON server
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    delta_short = datetime.timedelta(seconds=yellow_timeout)
    delta_long = datetime.timedelta(hours=red_timeout)
    
    try:
        last_value = StatusCache.objects.filter(instrument_id=instrument_id).latest('timestamp')
    except:
        logging.error("No cached status for instrument %s" % instrument_id.name)
        return 2
        
    if timezone.now()-last_value.timestamp>delta_long:
        return 2
    elif timezone.now()-last_value.timestamp>delta_short:
        return 1
    return 0

def get_completeness_status(instrument_id):
    """
        Check that the latest runs have successfully completed post-processing
        @param instrument_id: Instrument object
    """
    STATUS_OK = (0, "OK")
    STATUS_WARNING = (1, "Warning")
    STATUS_ERROR = (2, "Error")
    STATUS_UNKNOWN = (None, "Unknown")

    try:
        # Check for completeness of the three runs before the last run.
        # We don't use the last one because we may still be working on it.
        latest_runs = DataRun.objects.filter(instrument_id=instrument_id)

        # We need at least 4 runs for a meaningful status        
        if len(latest_runs)<4:    
            return STATUS_UNKNOWN
        
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
    if not request.GET.has_key('since') or not request.GET.has_key('complete_since'):
        return {}
    data_dict = {}
    
    # Get the last run ID that the client knows about
    since = request.GET.get('since', '0')
    refresh_needed = '1'
    try:
        since = int(since)
        since_run_id = get_object_or_404(DataRun, id=since)
    except:
        since = 0
        refresh_needed = '0'
        since_run_id = None
        
    # Get the earliest run that the client knows about
    complete_since = request.GET.get('complete_since', since)
    try:
        complete_since = int(complete_since)
    except:
        complete_since = 0
        
    if complete_since == 0:
        return {}
        
    # Get last experiment and last run
    run_list = DataRun.objects.filter(instrument_id=instrument_id, id__gte=complete_since).order_by('created_on').reverse()

    status_list = []
    if since_run_id is not None and len(run_list)>0:
        data_dict['last_run_id'] = run_list[0].id
        refresh_needed = '1' if since_run_id.created_on<run_list[0].created_on else '0'         
        update_list = []
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

    data_dict['refresh_needed'] = refresh_needed
    data_dict['status_list'] = status_list
    return data_dict


