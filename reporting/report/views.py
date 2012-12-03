from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from report.models import DataRun, RunStatus, WorkflowSummary, IPTS, Instrument
from icat_server_communication import get_run_info

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

    run_object = DataRun.objects.filter(run_number=run_id)
    if len(run_object)>0:
        run_object = run_object[0]

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
    last_expt_id = IPTS.objects.filter(instruments=instrument_id).order_by('created_on').reverse()[0]
    last_run_id = DataRun.objects.filter(ipts_id=last_expt_id).order_by('created_on').reverse()[0]
    
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
    
    ipts_ids = IPTS.objects.filter(expt_name=ipts)
    if len(ipts_ids)==0:
        raise Http404
    ipts_id = ipts_ids[0]
        
    # Get base URL
    base_url = reverse('report.views.detail',args=[instrument,'0000'])
    base_url = base_url.replace('/0000','')
    
    run_list, run_list_header = view_util.RunSorter(request)(ipts_id)
    
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
                                                           })