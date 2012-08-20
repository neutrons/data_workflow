from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from report.models import DataRun, RunStatus, WorkflowSummary, IPTS, Instrument

def summary(request):
    return HttpResponse("Summary view")

def detail(request, instrument, run_id):
    if instrument.upper() not in ['EQSANS']:
        return HttpResponse("[%s] is not a supported instrument" % instrument)
    
    run_object = DataRun.objects.filter(run_number=run_id)
    if len(run_object)>0:
        run_object = run_object[0]
    
    # Find status entries
    status_objects = RunStatus.objects.filter(run_id=run_object)
    return render_to_response('report/detail.html', {'instrument':instrument.upper(),
                                                     'run_id':run_id,
                                                     'status':status_objects,
                                                    })

def instrument_summary(request, instrument):
    
    # Get instrument
    instrument_id = Instrument.objects.find_instrument(instrument)
    if instrument_id is None:
        print "Raise a 404"
    
    # Get list of IPTS
    ipts = IPTS.objects.filter(instruments=instrument_id)
    
    # Get base URL
    base_url = reverse('report.views.ipts_summary',args=[instrument,'0000'])
    base_url = base_url.replace('/0000','')
    
    return render_to_response('report/instrument.html', {'instrument':instrument.upper(),
                                                         'ipts':ipts,
                                                         'base_ipts_url':base_url,
                                                         })
    
def ipts_summary(request, instrument, ipts):
    
    ipts_ids = IPTS.objects.filter(ipts_number=ipts)
    if len(ipts_ids)==0:
        print "Raise 404"
    ipts_id = ipts_ids[0]
        
    # Get base URL
    base_url = reverse('report.views.detail',args=[instrument,'0000'])
    base_url = base_url.replace('/0000','')
    
    run_list = DataRun.objects.filter(ipts_id=ipts_id)
    
    return render_to_response('report/ipts_summary.html', {'instrument':instrument.upper(),
                                                           'ipts_number':ipts,
                                                           'run_list':run_list,
                                                           'base_run_url':base_url,
                                                           })