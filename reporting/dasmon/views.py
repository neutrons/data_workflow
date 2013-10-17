"""
    Live monitoring
"""
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson, dateformat, timezone
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.template import Context, loader

from report.models import Instrument, DataRun, WorkflowSummary
from dasmon.models import Parameter, StatusVariable, StatusCache, ActiveInstrument

import view_util
import report.view_util
import users.view_util
import logging
import sys

@users.view_util.login_or_local_required
@cache_page(5)
@users.view_util.monitor
def summary(request):
    """
        List of available instruments
    """
    instruments = Instrument.objects.all().order_by('name')
    
    # Get the system health status
    postprocess_status = view_util.get_system_health()
    
    instrument_list = []
    for i in instruments:
        if not ActiveInstrument.objects.is_alive(i):
            continue
        if ActiveInstrument.objects.is_adara(i):
            dasmon_url = reverse('dasmon.views.live_monitor',args=[i.name])
        else:
            dasmon_url = reverse('dasmon.views.live_runs',args=[i.name])
        diagnostics_url = reverse('dasmon.views.diagnostics', args=[i.name])
        das_status = view_util.get_dasmon_status(i)
        pvstreamer_status = view_util.get_pvstreamer_status(i)
        completeness, message = view_util.get_completeness_status(i)
        instrument_list.append({'name': i.name,
                                'recording_status': view_util.is_running(i),
                                'url': dasmon_url,
                                'diagnostics_url': diagnostics_url,
                                'dasmon_status': das_status,
                                'pvstreamer_status': pvstreamer_status,
                                'completeness': completeness,
                                'completeness_msg': message
                                })
  
    breadcrumbs = "home"
    update_url = reverse('dasmon.views.summary_update')
    central_services_url = reverse('dasmon.views.diagnostics', args=['common'])
    template_values = {'instruments': instrument_list,
                       'breadcrumbs': breadcrumbs,
                       'postprocess_status': postprocess_status,
                       'update_url': update_url,
                       'central_services_url': central_services_url
                       }
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('dasmon/global_summary.html',
                              template_values)


@users.view_util.login_or_local_required
@cache_page(5)
@users.view_util.monitor
def activity_summary(request):
    """
        Run rates for all instruments
    """
    global_status_url = reverse('dasmon.views.summary',args=[])
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; activity" % global_status_url
    
    template_values = {'breadcrumbs': breadcrumbs,
                       'update_url': reverse('dasmon.views.activity_update'),
                       }
    
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('dasmon/activity_summary.html',
                              template_values)    
    
@cache_page(5)
def activity_update(request):
    instruments = Instrument.objects.all().order_by('name')
    #              YELLOW     ORANGE     TURQUOISE  PURPLE
    color_list = ['#FFFF73', '#BC2F2F', '#006363', '#48036F',
                  '#BFBF30', '#A66E00', '#009999', '#7109AA',
                  '#F1EF00', '#FFBE40', '#5CCCCC', '#AD66D5',
                  '#E5DBEB', '#E567B1', '#88B32D', '#4573D5'
                  ]
    instrument_list = []
    count = 0
    for i in instruments:
        if not ActiveInstrument.objects.is_alive(i):
            continue
        series = {'label':i.name,
                  'data':report.view_util.run_rate(i)}
        if count<len(color_list):
            series['color'] = color_list[count]
        instrument_list.append(series)
        count += 1
        
    return HttpResponse(simplejson.dumps({'run_rate':instrument_list}), mimetype="application/json")
    
        
@users.view_util.login_or_local_required
@cache_page(5)
@users.view_util.monitor
def live_monitor(request, instrument):
    """
        Display the list of latest errors
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Update URL
    update_url = reverse('dasmon.views.get_update',args=[instrument])
    pv_url = reverse('pvmon.views.get_update',args=[instrument])

    breadcrumbs = view_util.get_monitor_breadcrumbs(instrument_id)
    template_values = {'instrument': instrument.upper(),
                       'breadcrumbs':breadcrumbs,
                       'update_url': update_url,
                       'pv_url': pv_url,
                       'key_value_pairs': view_util.get_cached_variables(instrument_id, monitored_only=True),
                       }
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = view_util.fill_template_values(request, **template_values)
    
    template_values['signals_url'] = reverse('dasmon.views.get_signal_table',args=[instrument])
    
    return render_to_response('dasmon/live_monitor.html', template_values)
    
@users.view_util.login_or_local_required
@cache_page(5)
@users.view_util.monitor
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
        first_run = runs[len(runs)-1].id
    else:
        first_run = 0
        
    run_list = []
    for r in runs:
        status = view_util.get_run_status_text(r)
        run_list.append({'run_number':r.run_number,
                         'created_on':r.created_on,
                         'last_error':status,
                         'id':r.id})
    
    run_list_header = [{'name': 'Run', 'style':"min-width: 50px"},
                       {'name': 'Created on'},
                       {'name': 'Status'}]
    
    breadcrumbs = view_util.get_monitor_breadcrumbs(instrument_id)
    template_values = {'instrument':instrument.upper(),
                       'breadcrumbs':breadcrumbs,
                       'update_url':update_url,
                       'run_list':run_list,
                       'run_list_header':run_list_header,
                       'first_run_id':first_run
                       }
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = view_util.fill_template_values(request, **template_values)
    
    return render_to_response('dasmon/live_runs.html', template_values)
    
    
@users.view_util.login_or_local_required
@users.view_util.monitor
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
@cache_page(5)
@users.view_util.monitor
def diagnostics(request, instrument):
    """
        Diagnose the health of an instrument
        @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # DASMON
    dasmon_diag = view_util.dasmon_diagnostics(instrument_id)
    
    # PVStreamer
    pv_diag = view_util.pvstreamer_diagnostics(instrument_id)
    
    # Workflow Manager
    wf_diag = view_util.workflow_diagnostics()
    
    # Post-processing
    red_diag = view_util.postprocessing_diagnostics()
    
    # Actions messages
    actions = []
    if dasmon_diag['dasmon_listener_warning'] and pv_diag['dasmon_listener_warning'] \
        and wf_diag['dasmon_listener_warning']:
        actions.append("Multiple heartbeat message failures: restart dasmon_listener before proceeding")
    
    breadcrumbs = view_util.get_monitor_breadcrumbs(instrument_id, 'diagnostics')
    template_values = {'instrument':instrument.upper(),
                       'breadcrumbs':breadcrumbs,
                       }
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = view_util.fill_template_values(request, **template_values)
    
    template_values['dasmon_diagnostics'] = dasmon_diag
    template_values['pv_diagnostics'] = pv_diag
    template_values['wf_diagnostics'] = wf_diag
    template_values['post_diagnostics'] = red_diag
    template_values['action_messages'] = actions
    
    return render_to_response('dasmon/diagnostics.html', template_values)


@users.view_util.login_or_local_required
@cache_page(5)
def get_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
    """ 
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # Get last experiment and last run
    data_dict = report.view_util.get_current_status(instrument_id)      
    data_dict['variables'] = view_util.get_cached_variables(instrument_id, monitored_only=False)

    localtime = timezone.now()
    df = dateformat.DateFormat(localtime)
    recording_status = {"key": "recording_status",
                        "value": view_util.is_running(instrument_id),
                        "timestamp": df.format(settings.DATETIME_FORMAT),
                        }
    data_dict['variables'].append(recording_status)
    
    # Get current DAS health status
    das_status = view_util.get_system_health(instrument_id)
    data_dict['das_status'] = das_status
    data_dict['live_plot_data']=view_util.get_live_variables(request, instrument_id)
    
    # Recent run info
    data_dict = view_util.get_live_runs_update(request, instrument_id, None, **data_dict)
    
    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")


@users.view_util.login_or_local_required
@cache_page(5)
def summary_update(request):
    """
         Response to AJAX call to get updated health info for all instruments
    """
    # Get the system health status
    postprocess_status = view_util.get_system_health()
    
    instrument_list = []
    for i in Instrument.objects.all().order_by('name'):
        das_status = view_util.get_dasmon_status(i)
        pvstreamer_status = view_util.get_pvstreamer_status(i)
        completeness, message = view_util.get_completeness_status(i)
        instrument_list.append({'name': i.name,
                                'recording_status': view_util.is_running(i),
                                'dasmon_status': das_status,
                                'pvstreamer_status': pvstreamer_status,
                                'completeness': completeness,
                                'completeness_msg': message
                                })
  
    data_dict = {'instruments':instrument_list,
                 'postprocess_status':postprocess_status
                 }
    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")


@cache_page(5)
def get_signal_table(request, instrument):
    """
        Ajax call to get the signal table
    """
    # First check that the user is authenticated
    #if not request.user.is_authenticated():
    #    return HttpResponseForbidden()
    
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    t = loader.get_template('dasmon/signal_table.html')
    c = Context({
            'signals': view_util.get_signals(instrument_id),
        })
    resp = t.render(c)
    return HttpResponse(resp, mimetype="text/html")
