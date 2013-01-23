"""
    Live monitoring
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson

from report.views import confirm_instrument
from report.models import Instrument, IPTS, DataRun, Error

import view_util
import users.view_util

@users.view_util.login_or_local_required
@confirm_instrument
def live_instrument(request, instrument):
    """
        TODO: need to display only last 20 (+ link to rest)
        TODO: ajax call for updates
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
        
    filter = request.GET.get('show', 'recent').lower()
    show_all = filter=='all'
    try:
        n_max = int(filter)
    except:
        n_max = 20

    # Get list of errors
    errors, errors_header = view_util.ErrorSorter(request)(instrument_id)
    number_of_errors = len(errors)
    if not show_all and len(errors)>n_max:
        errors = errors[:n_max]
    
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
    
    # Instrument reporting URL
    instrument_url = reverse('report.views.instrument_summary',args=[instrument])
    error_url = reverse('monitor.views.live_instrument',args=[instrument])
    
    update_url = reverse('monitor.views.get_update',args=[instrument])
    
    # Get last error ID
    try:
        last_error = Error.objects.latest('run_status_id__created_on')
    except:
        last_error = None
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s" % (reverse('report.views.summary'),
                                                         instrument.lower()
                                                         ) 

    template_values = {'instrument':instrument.upper(),
                       'error_list':errors,
                       'error_header':errors_header,
                       'base_ipts_url':base_ipts_url,
                       'base_run_url':base_run_url,
                       'breadcrumbs':breadcrumbs,
                       'last_expt': last_expt_id,
                       'last_run': last_run_id,
                       'all_shown':show_all,
                       'number_shown':len(errors),
                       'number_of_errors':number_of_errors,
                       'instrument_url':instrument_url,
                       'error_url':error_url,
                       'update_url':update_url,
                       'last_error':last_error,
                       }
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('monitor/live_instrument.html', template_values)
    
@confirm_instrument
def get_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
         @param ipts: experiment name
    """ 
    since = request.GET.get('since', '0')
    try:
        since = int(since)
    except:
        data_dict = {"refresh_needed": '0'}
        return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")
    
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())    
    last_error_id = get_object_or_404(Error, id=since)
    
    errors = Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id).order_by('run_status_id__created_on').reverse()
    
    if len(errors)==0:
        data_dict = {"refresh_needed": '0'}
    else:
        refresh_needed = '1' if last_error_id.run_status_id.created_on<errors[0].run_status_id.created_on else '0'         
        data_dict = {"last_run": errors[0].run_status_id.run_id.run_number,
                     "refresh_needed": refresh_needed,
                     }

    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")
