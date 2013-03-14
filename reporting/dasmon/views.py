"""
    Live monitoring
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson, dateformat, timezone
from django.conf import settings
from django.views.decorators.cache import cache_page

from report.views import confirm_instrument
from report.models import Instrument
from dasmon.models import Parameter, StatusVariable, StatusCache

import view_util
import report.view_util
import users.view_util
import logging
import sys

def _get_status_variables(instrument, filter=True):
    """
        @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    keys = Parameter.objects.all().order_by('name')
    key_value_pairs = []
    for k in keys:
        if k.monitored is True or filter is False:
            try:
                last_value = view_util.get_latest(instrument_id, k)
                key_value_pairs.append(last_value)
            except:
                # Could not process key-value pair: skip
                logging.warning(sys.exc_value)
    return key_value_pairs

@users.view_util.login_or_local_required
@confirm_instrument
@cache_page(5)
def live_monitor(request, instrument):
    """
        Display the list of latest errors
        @param instrument: instrument name
    """
    key_value_pairs = _get_status_variables(instrument)
    
    # Instrument reporting URL
    instrument_url = reverse('report.views.instrument_summary',args=[instrument])
    error_url = reverse('report.views.live_errors',args=[instrument])
    
    update_url = reverse('dasmon.views.get_update',args=[instrument])
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse('report.views.summary'),
            reverse('report.views.instrument_summary',args=[instrument]), instrument, "DAS monitor"
            ) 

    template_values = {'instrument':instrument.upper(),
                       'breadcrumbs':breadcrumbs,
                       'instrument_url':instrument_url,
                       'error_url':error_url,
                       'update_url':update_url,
                       'key_value_pairs':key_value_pairs,
                       }
    template_values = view_util.get_run_status(**template_values)
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    
    # The DAS monitor link is filled out by report.view_util but we don't need it here
    template_values['dasmon_url'] = None
    
    return render_to_response('dasmon/live_monitor.html', template_values)
    
@users.view_util.login_or_local_required
@confirm_instrument
@cache_page(5)
def get_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
    """ 
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    key_value_pairs = _get_status_variables(instrument, False)
    
    # Get last experiment and last run
    data_dict = report.view_util.get_current_status(instrument_id)  
    data_dict['variables'] = []
    if len(key_value_pairs)>0:
        variable_list = []
        for kvp in key_value_pairs:
            localtime = timezone.localtime(kvp.timestamp)
            df = dateformat.DateFormat(localtime)
            
            # Check whether we have a number
            try:
                float_value = float(kvp.value)
                string_value = '%g' % float_value
            except:
                string_value = kvp.value
            
            variable_dict = {"key": str(kvp.key_id),
                             "value": string_value,
                             "timestamp": df.format(settings.DATETIME_FORMAT),
                             }
            variable_list.append(variable_dict)    
        data_dict['variables'] = variable_list
    
    localtime = timezone.now()
    df = dateformat.DateFormat(localtime)
    recording_status = {"key": "recording_status",
                        "value": view_util.is_running(instrument_id),
                        "timestamp": df.format(settings.DATETIME_FORMAT),
                        }
    data_dict['variables'].append(recording_status)
    
    data_dict['live_plot_data']=view_util.get_live_variables(request, instrument_id)

    return HttpResponse(simplejson.dumps(data_dict), mimetype="application/json")