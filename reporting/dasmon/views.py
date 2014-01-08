"""
    Live monitoring
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson, dateformat, timezone
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.template import Context, loader

from report.models import Instrument, DataRun
from dasmon.models import ActiveInstrument
from users.models import SiteNotification

import view_util
import report.view_util
import users.view_util
import legacy_status

@users.view_util.login_or_local_required
#@cache_page(60)
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
        is_adara = ActiveInstrument.objects.is_adara(i)
        if not ActiveInstrument.objects.is_alive(i):
            continue
        if is_adara:
            dasmon_url = reverse('dasmon.views.live_monitor',args=[i.name])
            das_status = view_util.get_dasmon_status(i)
            pvstreamer_status = view_util.get_pvstreamer_status(i)
        else:
            dasmon_url = reverse('dasmon.views.live_runs',args=[i.name])
            das_status = -1
            pvstreamer_status = -1
        diagnostics_url = reverse('dasmon.views.diagnostics', args=[i.name])
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
@cache_page(60)
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
    
@cache_page(15)
def activity_update(request):
    instruments = Instrument.objects.all().order_by('name')
    #              YELLOW     ORANGE     TURQUOISE  PURPLE
    color_list = ['#FFFF73', '#BC2F2F', '#006363', '#48036F',
                  '#BFBF30', '#A66E00', '#009999', '#7109AA',
                  '#F1EF00', '#FFBE40', '#5CCCCC', '#AD66D5',
                  '#E5DBEB', '#E567B1', '#88B32D', '#4573D5'
                  ]
    instrument_list = []
    total_rate = [[-j, 0] for j in range(24)]
    count = 0
    for i in instruments:
        if not ActiveInstrument.objects.is_alive(i):
            continue
        rate = report.view_util.run_rate(i)
        rate_corrected = [[-j, 0] for j in range(24)]
        for pt in rate:
            for rc in rate_corrected:
                if rc[0]==pt[0]:
                    rc[1] = pt[1]
        
        for j in range(24):
            total_rate[j][1] += rate_corrected[j][1]
            
        series = {'label':i.name,
                  'data':rate_corrected}
        if count<len(color_list):
            series['color'] = color_list[count]
        instrument_list.append(series)
        count += 1
        
    instrument_list.append({'label': '',
                            'data': total_rate,
                            'color': '#aaaaaa',
                            'stack': 0,
                            'bars': {'fill': 0}})
        
    response = HttpResponse(simplejson.dumps({'run_rate':instrument_list}), content_type="application/json")
    response['Connection'] = 'close'
    return response
    
@users.view_util.login_or_local_required
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@users.view_util.monitor
def legacy_monitor(request, instrument):
    """
        For legacy instruments, show contents of old status page
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    update_url = reverse('dasmon.views.get_update',args=[instrument])
    legacy_update_url = reverse('dasmon.views.get_legacy_data',args=[instrument])
    breadcrumbs = view_util.get_monitor_breadcrumbs(instrument_id)
    kvp = legacy_status.get_ops_status(instrument_id)
    template_values = {'instrument': instrument.upper(),
                       'breadcrumbs':breadcrumbs,
                       'update_url': update_url,
                       'legacy_update_url': legacy_update_url,
                       'key_value_pairs':kvp}
    if len(kvp)==0:
        inst_url = legacy_status.get_legacy_url(instrument_id)
        template_values['user_alert'] = ["Could not connect to <a href='%s'>%s</a>" % (inst_url, inst_url)]
    for group in kvp:
        for item in group['data']:
            if item['key'] in ['Proposal', 'Detector_Rate', 'Run', 'Status']:
                template_values[item['key']] = item['value']
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = view_util.fill_template_values(request, **template_values)
    return render_to_response('dasmon/legacy_monitor.html', template_values)

@users.view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_legacy_data(request, instrument):
    """
        Return the latest legacy status information
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    data_dict = legacy_status.get_ops_status(instrument_id)
    response = HttpResponse(simplejson.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response

@users.view_util.login_or_local_required
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@users.view_util.monitor
def live_monitor(request, instrument):
    """
        Display the list of current DASMON status
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
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@users.view_util.monitor
def live_runs(request, instrument):
    """
        Display the list of latest runs
        @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # Update URL
    update_url = reverse('dasmon.views.get_update',args=[instrument])

    # Get the latest runs
    runs = DataRun.objects.filter(instrument_id=instrument_id).order_by("id").reverse()[:20]
    if len(runs)>0:
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
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@users.view_util.monitor
def diagnostics(request, instrument):
    """
        Diagnose the health of an instrument
        @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Workflow Manager
    wf_diag = view_util.workflow_diagnostics()
    # Post-processing
    red_diag = view_util.postprocessing_diagnostics()
    
    breadcrumbs = view_util.get_monitor_breadcrumbs(instrument_id, 'diagnostics')
    template_values = {'instrument':instrument.upper(),
                       'breadcrumbs':breadcrumbs,
                       }
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = view_util.fill_template_values(request, **template_values)
    
    actions = []
    if ActiveInstrument.objects.is_adara(instrument_id):
        # DASMON
        dasmon_diag = view_util.dasmon_diagnostics(instrument_id)
        # PVStreamer
        pv_diag = view_util.pvstreamer_diagnostics(instrument_id)
        # Actions messages
        if dasmon_diag['dasmon_listener_warning'] and pv_diag['dasmon_listener_warning'] \
            and wf_diag['dasmon_listener_warning']:
            actions.append("Multiple heartbeat message failures: restart dasmon_listener before proceeding")
        template_values['dasmon_diagnostics'] = dasmon_diag
        template_values['pv_diagnostics'] = pv_diag

    template_values['wf_diagnostics'] = wf_diag
    template_values['post_diagnostics'] = red_diag
    template_values['action_messages'] = actions
    
    notices = []
    for item in SiteNotification.objects.filter(is_active=True):
        notices.append(item.message)
    if len(notices)>0:
        template_values['user_alert'] = notices

    return render_to_response('dasmon/diagnostics.html', template_values)


@users.view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
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
    response = HttpResponse(simplejson.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    response['Content-Length'] = len(response.content)
    return response


@users.view_util.login_or_local_required_401
@cache_page(15)
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
    response = HttpResponse(simplejson.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    response['Content-Length'] = len(response.content)
    return response


@users.view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_signal_table(request, instrument):
    """
        Ajax call to get the signal table
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    t = loader.get_template('dasmon/signal_table.html')
    c = Context({
            'signals': view_util.get_signals(instrument_id),
        })
    resp = t.render(c)
    response = HttpResponse(resp, content_type="text/html")
    response['Connection'] = 'close'
    response['Content-Length'] = len(response.content)
    return response
