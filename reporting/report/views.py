from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson, dateformat, timezone
from django.conf import settings

from report.models import DataRun, RunStatus, WorkflowSummary, IPTS, Instrument
from icat_server_communication import get_run_info, get_ipts_info

import view_util
import users.view_util
import monitor.view_util

def confirm_instrument(view):
    """
        Decorator to verify that the instrument parameter is valid
    """
    def validated_view(request, instrument, *args, **kws):
        # Verify that the requested data exists 
        get_object_or_404(Instrument, name=instrument.lower())
        return view(request, instrument, *args, **kws)
        
    return validated_view   

@users.view_util.login_or_local_required
def summary(request):
    """
        List of available instruments
    """
    instruments = Instrument.objects.all().order_by('name')
    # Get base URL
    base_url = reverse('report.views.instrument_summary',args=['aaaa'])
    base_url = base_url.replace('/aaaa','')
    breadcrumbs = "home"

    template_values = {'instruments':instruments,
                       'breadcrumbs':breadcrumbs,
                       'base_instrument_url':base_url}
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/global_summary.html',
                              template_values)

@users.view_util.login_or_local_required
@confirm_instrument
def detail(request, instrument, run_id):
    """
        Run details
        @param instrument: instrument name
        @param run_id: run number, as string
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    run_object = get_object_or_404(DataRun, instrument_id=instrument_id,run_number=run_id)

    icat_info = get_run_info(instrument, str(run_object.ipts_id), run_id)
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; run %s" % (reverse('report.views.summary'),
            reverse('report.views.instrument_summary',args=[instrument]), instrument,
            reverse('report.views.ipts_summary',args=[instrument, run_object.ipts_id.expt_name]), str(run_object.ipts_id).lower(),  
            run_id          
            ) 
    
    # Find status entries
    status_objects, status_header = view_util.ActivitySorter(request)(run_object)
    
    template_values = {'instrument':instrument.upper(),
                       'run_object':run_object,
                       'status':status_objects,
                       'status_header':status_header,
                       'breadcrumbs':breadcrumbs,
                       'icat_info':icat_info,
                       }
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/detail.html', template_values)

@users.view_util.login_or_local_required
def instrument_summary(request, instrument):
    """
        Instrument summary page
        @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # Get list of IPTS
    ipts, ipts_header = view_util.ExperimentSorter(request)(instrument_id)    
    
    # Get base IPTS URL
    base_ipts_url = reverse('report.views.ipts_summary',args=[instrument,'0000'])
    base_ipts_url = base_ipts_url.replace('/0000','')
    
    # Get base Run URL
    base_run_url = reverse('report.views.detail',args=[instrument,'0000'])
    base_run_url = base_run_url.replace('/0000','')
    
    # Get last experiment and last run
    last_run_id = DataRun.objects.get_last_run(instrument_id)
    if last_run_id is None:
        last_expt_id = IPTS.objects.get_last_ipts(instrument_id)
    else:
        last_expt_id = last_run_id.ipts_id
    
    # Instrument error URL
    try:
        error_url = reverse('monitor.views.live_errors',args=[instrument])
    except:
        error_url = None

    # Get run rate and error rate
    run_rate = monitor.view_util.run_rate(instrument_id)
    error_rate = monitor.view_util.error_rate(instrument_id)
    update_url = reverse('report.views.get_instrument_update',args=[instrument])
    
    # Get the last IPTS created so that we can properly do the live update
    last_expt_created = IPTS.objects.get_last_ipts(instrument_id)
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s" % (reverse('report.views.summary'),
                                                         instrument.lower()
                                                         ) 

    template_values = {'instrument':instrument.upper(),
                       'ipts':ipts,
                       'ipts_header':ipts_header,
                       'base_ipts_url':base_ipts_url,
                       'base_run_url':base_run_url,
                       'breadcrumbs':breadcrumbs,
                       'last_expt': last_expt_id,
                       'last_run': last_run_id,
                       'error_url': error_url,
                       'update_url':update_url,
                       'last_expt_created':last_expt_created,
                       'run_rate':str(run_rate),
                       'error_rate':str(error_rate),
                       }
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/instrument.html', template_values)

@users.view_util.login_or_local_required
@confirm_instrument
def ipts_summary(request, instrument, ipts):
    """
        Experiment summary giving the list of runs
        @param instrument: instrument name
        @param ipts: experiment name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    # Get experiment
    ipts_id = get_object_or_404(IPTS, expt_name=ipts, instruments=instrument_id)
    
    filter = request.GET.get('show', 'recent').lower()
    show_all = filter=='all'
    try:
        n_max = int(filter)
    except:
        n_max = 20
    number_of_runs = ipts_id.number_of_runs()
    
    icat_info = get_ipts_info(instrument, ipts)

    # Get base IPTS URL
    base_ipts_url = reverse('report.views.ipts_summary',args=[instrument,'0000'])
    base_ipts_url = base_ipts_url.replace('/0000','')

    # Get base URL
    base_url = reverse('report.views.detail',args=[instrument,'0000'])
    base_url = base_url.replace('/0000','')
    ipts_url = reverse('report.views.ipts_summary',args=[instrument,ipts])
    update_url = reverse('report.views.get_experiment_update',args=[instrument,ipts])

    # Get the latest run and experiment so we can determine later
    # whether the user should refresh the page
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    # Get last experiment and last run
    last_run_id = DataRun.objects.get_last_run(instrument_id)
    if last_run_id is None:
        last_expt_id = IPTS.objects.get_last_ipts(instrument_id)
    else:
        last_expt_id = last_run_id.ipts_id
    
    run_list, run_list_header = view_util.RunSorter(request)(ipts_id, 
                                                             show_all=show_all,
                                                             n_shown=n_max)
    
    # Get run rate and error rate
    run_rate = monitor.view_util.run_rate(instrument_id)
    error_rate = monitor.view_util.error_rate(instrument_id)

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse('report.views.summary'),
            reverse('report.views.instrument_summary',args=[instrument]), instrument,
            str(ipts_id).lower()
            ) 

    template_values = {'instrument':instrument.upper(),
                       'ipts_number':ipts,
                       'run_list':run_list,
                       'run_list_header':run_list_header,
                       'base_run_url':base_url,
                       'base_ipts_url':base_ipts_url,
                       'breadcrumbs':breadcrumbs,
                       'icat_info':icat_info,
                       'all_shown':show_all,
                       'number_shown':len(run_list),
                       'number_of_runs':number_of_runs,
                       'ipts_url':ipts_url,
                       'update_url':update_url,
                       'last_run':last_run_id,
                       'last_expt':last_expt_id,
                       'run_rate':str(run_rate),
                       'error_rate':str(error_rate),
                       }
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/ipts_summary.html', template_values)
    
@users.view_util.login_or_local_required
@confirm_instrument
def get_experiment_update(request, instrument, ipts):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
         @param ipts: experiment name
    """ 
    since = request.GET.get('since', '0')
    refresh_needed = '1'
    try:
        since = int(since)
        since_run_id = get_object_or_404(DataRun, id=since)
    except:
        refresh_needed = '0'
        since_run_id = None
    
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    # Get experiment
    ipts_id = get_object_or_404(IPTS, expt_name=ipts, instruments=instrument_id)
    
    # Get last experiment and last run
    data_dict = monitor.view_util.get_current_status(instrument_id)    
    run_list = DataRun.objects.filter(instrument_id=instrument_id, ipts_id=ipts_id).order_by('created_on').reverse()

    if since_run_id is not None and len(run_list)>0:
        data_dict['last_run_id'] = run_list[0].id
        refresh_needed = '1' if since_run_id.created_on<run_list[0].created_on else '0'         
        update_list = []
        for r in run_list:
            if since_run_id.created_on < r.created_on:
                localtime = timezone.localtime(r.created_on)
                df = dateformat.DateFormat(localtime)
                expt_dict = {"run":r.run_number,
                            "timestamp":df.format(settings.DATETIME_FORMAT),
                            "last_error":"",
                            "run_id":str(r.id),
                            }
                if r.last_error() is not None:
                    expt_dict["last_error"] = r.last_error()
                update_list.append(expt_dict)
        data_dict['run_list'] = update_list

    data_dict['refresh_needed'] = refresh_needed
    
    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")


@users.view_util.login_or_local_required
@confirm_instrument
def get_instrument_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
    """ 
    since = request.GET.get('since', '0')
    refresh_needed = '1'
    try:
        since = int(since)
        since_expt_id = get_object_or_404(IPTS, id=since)
    except:
        refresh_needed = '0'
        since_expt_id = None
    
    # Get the instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # Get last experiment and last run
    data_dict = monitor.view_util.get_current_status(instrument_id)
    expt_list = IPTS.objects.filter(instruments=instrument_id).order_by('created_on').reverse()

    if since_expt_id is not None and len(expt_list)>0:
        data_dict['last_expt_id'] = expt_list[0].id
        refresh_needed = '1' if since_expt_id.created_on<expt_list[0].created_on else '0'         
        update_list = []
        for e in expt_list:
            if since_expt_id.created_on < e.created_on:
                localtime = timezone.localtime(e.created_on)
                df = dateformat.DateFormat(localtime)
                expt_dict = {"ipts":e.expt_name.upper(),
                            "n_runs":e.number_of_runs(),
                            "timestamp":df.format(settings.DATETIME_FORMAT),
                            "ipts_id":e.id,
                            }
                update_list.append(expt_dict)
        data_dict['expt_list'] = update_list

    data_dict['refresh_needed'] = refresh_needed
    
    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")
