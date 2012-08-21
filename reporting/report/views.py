from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from report.models import DataRun, RunStatus, WorkflowSummary, IPTS, Instrument

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

    return render_to_response('report/global_summary.html', {'instruments':instruments,
                                                             'base_instrument_url':base_url})

@confirm_instrument
def detail(request, instrument, run_id):

    run_object = DataRun.objects.filter(run_number=run_id)
    if len(run_object)>0:
        run_object = run_object[0]

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; run %s" % (reverse('report.views.summary'),
            reverse('report.views.instrument_summary',args=[instrument]), instrument,
            reverse('report.views.ipts_summary',args=[instrument, run_object.ipts_id.ipts_number]), str(run_object.ipts_id).lower(),  
            run_id          
            ) 
    
    # Find status entries
    status_objects = RunStatus.objects.filter(run_id=run_object)
    return render_to_response('report/detail.html', {'instrument':instrument.upper(),
                                                     'run_object':run_object,
                                                     'status':status_objects,
                                                     'breadcrumbs':breadcrumbs,
                                                    })

def instrument_summary(request, instrument):
    
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # Get list of IPTS
    ipts = IPTS.objects.filter(instruments=instrument_id).order_by('ipts_number')
    
    # Get base URL
    base_url = reverse('report.views.ipts_summary',args=[instrument,'0000'])
    base_url = base_url.replace('/0000','')
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s" % (reverse('report.views.summary'),
                                                         instrument.lower()
            ) 

    return render_to_response('report/instrument.html', {'instrument':instrument.upper(),
                                                         'ipts':ipts,
                                                         'base_ipts_url':base_url,
                                                         'breadcrumbs':breadcrumbs,
                                                         })

@confirm_instrument
def ipts_summary(request, instrument, ipts):
    
    ipts_ids = IPTS.objects.filter(ipts_number=ipts)
    if len(ipts_ids)==0:
        raise Http404
    ipts_id = ipts_ids[0]
        
    # Get base URL
    base_url = reverse('report.views.detail',args=[instrument,'0000'])
    base_url = base_url.replace('/0000','')
    
    run_list = DataRun.objects.filter(ipts_id=ipts_id).order_by('run_number')
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse('report.views.summary'),
            reverse('report.views.instrument_summary',args=[instrument]), instrument,
            str(ipts_id).lower()
            ) 

    return render_to_response('report/ipts_summary.html', {'instrument':instrument.upper(),
                                                           'ipts_number':ipts,
                                                           'run_list':run_list,
                                                           'base_run_url':base_url,
                                                           'breadcrumbs':breadcrumbs,
                                                           })