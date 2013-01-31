"""
    Live monitoring
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson, dateformat, timezone
from django.conf import settings

from report.views import confirm_instrument
from report.models import Instrument, IPTS, DataRun, Error

import view_util
import users.view_util

@users.view_util.login_or_local_required
@confirm_instrument
def live_errors(request, instrument):
    """
        Display the list of latest errors
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
    error_url = reverse('monitor.views.live_errors',args=[instrument])
    
    update_url = reverse('monitor.views.get_update',args=[instrument])
    
    # Get last error ID
    try:
        last_error = Error.objects.latest('run_status_id__created_on')
    except:
        last_error = None
    
    # Get run rate and error rate
    run_rate = view_util.run_rate(instrument_id)
    error_rate = view_util.error_rate(instrument_id)
    
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
                       'run_rate':str(run_rate),
                       'error_rate':str(error_rate),
                       }
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('monitor/live_errors.html', template_values)
    
@confirm_instrument
def get_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
         @param ipts: experiment name
    """ 
    since = request.GET.get('since', '0')
    refresh_needed = '1'
    try:
        since = int(since)
        last_error_id = get_object_or_404(Error, id=since)
    except:
        refresh_needed = '0'
        last_error_id = None
    
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())    
    
    # Get last experiment and last run
    data_dict = view_util.get_current_status(instrument_id)    
    errors = Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id).order_by('run_status_id__created_on').reverse()
    
    
    if last_error_id is not None and len(errors)>0:
        data_dict['last_error_id'] = errors[0].id
        refresh_needed = '1' if last_error_id.run_status_id.created_on<errors[0].run_status_id.created_on else '0'         
        err_list = []
        for e in errors:
            if last_error_id.run_status_id.created_on<e.run_status_id.created_on:
                localtime = timezone.localtime(e.run_status_id.created_on)
                df = dateformat.DateFormat(localtime)
                err_dict = {"run":e.run_status_id.run_id.run_number,
                            "ipts":e.run_status_id.run_id.ipts_id.expt_name,
                            "description":e.description,
                            "timestamp":df.format(settings.DATETIME_FORMAT),
                            "error_id":e.id,
                            }
                err_list.append(err_dict)    
        data_dict['errors'] = err_list
    
    data_dict['refresh_needed'] = refresh_needed
    
    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")
