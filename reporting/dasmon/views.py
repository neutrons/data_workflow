"""
    Live monitoring
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson, dateformat, timezone
from django.conf import settings
from django.views.decorators.cache import cache_page

from report.views import confirm_instrument
from report.models import Instrument, DataRun, WorkflowSummary
from dasmon.models import Parameter, StatusVariable, StatusCache

import view_util
import report.view_util
import users.view_util
import logging
import sys

def _get_status_variables(instrument, filter=True):
    """
        @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    keys = Parameter.objects.all().order_by('name')
    key_value_pairs = []
    for k in keys:
        if k.monitored is True or filter is False:
            try:
                last_value = view_util.get_latest(instrument_id, k)
                key_value_pairs.append(last_value)
            except:
                # Could not process key-value pair: skip
                logging.warning(sys.exc_value)
    return key_value_pairs

@users.view_util.login_or_local_required
@confirm_instrument
@cache_page(5)
def live_monitor(request, instrument):
    """
        Display the list of latest errors
        @param instrument: instrument name
    """
    # Update URL
    update_url = reverse('dasmon.views.get_update',args=[instrument])
    
    template_values = {'instrument':instrument.upper(),
                       'update_url':update_url,
                       'key_value_pairs':_get_status_variables(instrument),
                       }
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = view_util.get_run_status(**template_values)
    
    template_values['live_runs_url'] = reverse('dasmon.views.live_runs',args=[instrument])
    
    return render_to_response('dasmon/live_monitor.html', template_values)
    
@users.view_util.login_or_local_required
@confirm_instrument
@cache_page(5)
def live_runs(request, instrument):
    """
        Display the list of latest errors
        @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # Update URL
    update_url = reverse('dasmon.views.get_update',args=[instrument])

    # Get the latest runs
    runs = DataRun.objects.filter(instrument_id=instrument_id)                               
    count = runs.count()
    runs = runs[count-20:count]
    run_list = []
    for r in runs:
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
        run_list.insert(0, {'run_number':r.run_number,
                            'created_on':r.created_on,
                            'last_error':status,
                            'id':r.id})
    
    run_list_header = [{'name': 'Run', 'style':"min-width: 50px"},
                       {'name': 'Created on'},
                       {'name': 'Status'}]
    
    template_values = {'instrument':instrument.upper(),
                       'update_url':update_url,
                       'run_list':run_list,
                       'run_list_header':run_list_header,
                       'first_run_id':runs[0].id
                       }
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = view_util.get_run_status(**template_values)
    
    template_values['live_monitor_url'] = reverse('dasmon.views.live_monitor',args=[instrument])
    
    return render_to_response('dasmon/live_runs.html', template_values)
    
@users.view_util.login_or_local_required
@confirm_instrument
@cache_page(5)
def get_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
    """ 
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    key_value_pairs = _get_status_variables(instrument, False)
    
    # Get last experiment and last run
    data_dict = report.view_util.get_current_status(instrument_id)  
    data_dict['variables'] = []
    if len(key_value_pairs)>0:
        variable_list = []
        for kvp in key_value_pairs:
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
            variable_list.append(variable_dict)    
        data_dict['variables'] = variable_list
    
    localtime = timezone.now()
    df = dateformat.DateFormat(localtime)
    recording_status = {"key": "recording_status",
                        "value": view_util.is_running(instrument_id),
                        "timestamp": df.format(settings.DATETIME_FORMAT),
                        }
    data_dict['variables'].append(recording_status)
    
    # Get current DAS health status
    das_status = report.view_util.get_post_processing_status()
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    das_status['dasmon'] = view_util.get_dasmon_status(instrument_id)
    data_dict['das_status'] = das_status
    
    data_dict['live_plot_data']=view_util.get_live_variables(request, instrument_id)
    
    # Recent run info
    run_dict = get_live_runs_update(request, instrument_id)
    for k in run_dict:
        data_dict[k] = run_dict[k]
    
    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")


def get_live_runs_update(request, instrument_id):
    """
         Get updated information about the latest runs
         @param request: HTTP request so we can get the 'since' parameter
         @param instrument_id: Instrument model object
    """ 
    data_dict = {}
    
    # Get the last run ID that the client knows about
    since = request.GET.get('since', '0')
    refresh_needed = '1'
    try:
        since = int(since)
        since_run_id = get_object_or_404(DataRun, id=since)
    except:
        refresh_needed = '0'
        since_run_id = None
        
    # Get the earliest run that the client knows about
    complete_since = request.GET.get('complete_since', since)
    try:
        complete_since = int(complete_since)
    except:
        complete_since = 0
        
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