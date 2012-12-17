from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson

from report.models import DataRun, RunStatus, WorkflowSummary, IPTS, Instrument
from icat_server_communication import get_run_info, get_ipts_info

import view_util

def confirm_instrument(view):
    """
        Decorator to verify that the instrument parameter is valid
    """
    def validated_view(request, instrument, *args, **kws):
        # Verify that the requested data exists 
        get_object_or_404(Instrument, name=instrument.lower())
        return view(request, instrument, *args, **kws)
        
    return validated_view   

def summary(request):
    """
        List of available instruments
    """
    instruments = Instrument.objects.all().order_by('name')
    # Get base URL
    base_url = reverse('report.views.instrument_summary',args=['aaaa'])
    base_url = base_url.replace('/aaaa','')
    breadcrumbs = "home"

    return render_to_response('report/global_summary.html', {'instruments':instruments,
                                                             'breadcrumbs':breadcrumbs,
                                                             'base_instrument_url':base_url})

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
    return render_to_response('report/detail.html', {'instrument':instrument.upper(),
                                                     'run_object':run_object,
                                                     'status':status_objects,
                                                     'status_header':status_header,
                                                     'breadcrumbs':breadcrumbs,
                                                     'icat_info':icat_info,
                                                    })

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
    last_expt_id = view_util.get_last_ipts(instrument_id)
    last_run_id = view_util.get_last_run(instrument_id, last_expt_id)
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s" % (reverse('report.views.summary'),
                                                         instrument.lower()
            ) 

    return render_to_response('report/instrument.html', {'instrument':instrument.upper(),
                                                         'ipts':ipts,
                                                         'ipts_header':ipts_header,
                                                         'base_ipts_url':base_ipts_url,
                                                         'base_run_url':base_run_url,
                                                         'breadcrumbs':breadcrumbs,
                                                         'last_expt': last_expt_id,
                                                         'last_run': last_run_id,
                                                         })

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
    number_of_runs = ipts_id.number_of_runs()
    
    icat_info = get_ipts_info(instrument, ipts)
        
    # Get base URL
    base_url = reverse('report.views.detail',args=[instrument,'0000'])
    base_url = base_url.replace('/0000','')
    ipts_url = reverse('report.views.ipts_summary',args=[instrument,ipts])
    update_url = reverse('report.views.get_update',args=[instrument,ipts])

    # Get the latest run and experiment so we can determine later
    # whether the user should refresh the page
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    last_expt_id = view_util.get_last_ipts(instrument_id)
    last_run_id = view_util.get_last_run(instrument_id, last_expt_id)
    
    run_list, run_list_header = view_util.RunSorter(request)(ipts_id, show_all=show_all)
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse('report.views.summary'),
            reverse('report.views.instrument_summary',args=[instrument]), instrument,
            str(ipts_id).lower()
            ) 

    return render_to_response('report/ipts_summary.html', {'instrument':instrument.upper(),
                                                           'ipts_number':ipts,
                                                           'run_list':run_list,
                                                           'run_list_header':run_list_header,
                                                           'base_run_url':base_url,
                                                           'breadcrumbs':breadcrumbs,
                                                           'icat_info':icat_info,
                                                           'all_shown':show_all,
                                                           'number_shown':len(run_list),
                                                           'number_of_runs':number_of_runs,
                                                           'ipts_url':ipts_url,
                                                           'update_url':update_url,
                                                           'last_run':last_run_id,
                                                           'last_expt':last_expt_id,
                                                           })
    
@confirm_instrument
def get_update(request, instrument, ipts):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
         @param ipts: experiment name
    """ 
    since = request.GET.get('since', '0')
    
    # Get the latest run and check whether new runs have happened since
    # the specified run number
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    ipts_id = get_object_or_404(IPTS, expt_name=ipts, instruments=instrument_id)
    last_run_id = view_util.get_last_run(instrument_id, ipts_id)
    if last_run_id is None:
        data_dict = {"refresh_needed": '0'}
    else:
        refresh_needed = '1' if int(since)<last_run_id.run_number else '0'         
        data_dict = {"last_run": last_run_id.run_number,
                     "refresh_needed": refresh_needed,
                     }

    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")
