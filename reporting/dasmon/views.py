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

@users.view_util.login_or_local_required
@cache_page(5)
def summary(request):
    """
        List of available instruments
    """
    instruments = Instrument.objects.all().order_by('name')
    
    # Get the system health status
    postprocess_status = report.view_util.get_post_processing_status()
    
    instrument_list = []
    for i in instruments:
        dasmon_url = reverse('dasmon.views.live_monitor',args=[i.name])
        das_status = view_util.get_dasmon_status(i)
        completeness, message = view_util.get_completeness_status(i)
        instrument_list.append({'name': i.name,
                                'url': dasmon_url,
                                'dasmon_status': das_status,
                                'completeness': completeness,
                                'completeness_msg': message
                                })
  
    breadcrumbs = "home"
    update_url = reverse('dasmon.views.summary_update')
    template_values = {'instruments':instrument_list,
                       'breadcrumbs':breadcrumbs,
                       'postprocess_status':postprocess_status,
                       'update_url':update_url
                       }
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('dasmon/global_summary.html',
                              template_values)


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
    
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    key_value_pairs = StatusCache.objects.filter(instrument_id=instrument_id).order_by("key_id__name")

    template_values = {'instrument':instrument.upper(),
                       'update_url':update_url,
                       'key_value_pairs':key_value_pairs,
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
    if len(runs)>0:
        nmax = min(20, len(runs))
        runs = runs.order_by("id").reverse()[:nmax]
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
        run_list.append({'run_number':r.run_number,
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
                       'first_run_id':runs[len(runs)-1].id
                       }
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = view_util.get_run_status(**template_values)
    
    template_values['live_monitor_url'] = reverse('dasmon.views.live_monitor',args=[instrument])
    
    return render_to_response('dasmon/live_runs.html', template_values)
    
    
@users.view_util.login_or_local_required
def help(request):
    
    global_status_url = reverse('dasmon.views.summary',args=[])
    hysa_live_monitor_url = reverse('dasmon.views.live_monitor', args=['hysa'])
    hysa_live_runs_url = reverse('dasmon.views.live_runs', args=['hysa'])

    breadcrumbs = "<a href='%s'>home</a> &rsaquo; help" % global_status_url
    
    template_values = {'global_status_url': global_status_url,
                       'hysa_live_monitor_url': hysa_live_monitor_url,
                       'hysa_live_runs_url': hysa_live_runs_url,
                       'breadcrumbs': breadcrumbs,
                       }
    template_values = users.view_util.fill_template_values(request, **template_values)
    
    return render_to_response('dasmon/help.html', template_values)

    
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
    key_value_pairs = StatusCache.objects.filter(instrument_id=instrument_id)
    
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
    run_dict = view_util.get_live_runs_update(request, instrument_id)
    for k in run_dict:
        data_dict[k] = run_dict[k]
    
    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")


@users.view_util.login_or_local_required
@cache_page(5)
def summary_update(request):
    """
         Response to AJAX call to get updated health info for all instruments
    """
    # Get the system health status
    postprocess_status = report.view_util.get_post_processing_status()
    
    instrument_list = []
    for i in Instrument.objects.all().order_by('name'):
        das_status = view_util.get_dasmon_status(i)
        completeness, message = view_util.get_completeness_status(i)
        instrument_list.append({'name': i.name, 
                                'dasmon_status': das_status,
                                'completeness': completeness,
                                'completeness_msg': message
                                })
  
    data_dict = {'instruments':instrument_list,
                 'postprocess_status':postprocess_status
                 }
    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")


