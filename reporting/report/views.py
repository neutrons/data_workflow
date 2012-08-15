from django.http import HttpResponse
from django.shortcuts import render_to_response

from report.models import DataRun, RunStatus

def summary(request):
    return HttpResponse("Summary view")

def detail(request, instrument, run_id):
    if instrument.upper() not in ['EQSANS']:
        return HttpResponse("[%s] is not a supported instrument" % instrument)
    
    run_object = DataRun.objects.filter(run_number=run_id)
    if len(run_object)>0:
        run_object = run_object[0]
    
    reply = "Details for run %s\n" % run_id
    
    # Find status entries
    status_objects = RunStatus.objects.filter(run_id=run_object)
    return render_to_response('report/detail.html', {'run_id':run_id,
                                                     'status':status_objects,
                                                    })
    return HttpResponse(reply)

def instrument_summary(request, instrument):
    return HttpResponse("%s summary view" % instrument)