"""
    Automated reduction configuration view
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.utils import dateparse, timezone
from models import ReductionProperty, PropertyModification
from report.models import Instrument
import logging
import json
import sys
import datetime

import users.view_util
import dasmon.view_util
import reporting_app.view_util

@users.view_util.login_or_local_required
def configuration(request, instrument):
    """
        View current automated reduction configuration and modification history
        for a given instrument
        
        @param request: request object
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    props_list = ReductionProperty.objects.filter(instrument=instrument_id)
    params_list = []
    for item in props_list:
        params_list.append({"key": str(item.key),
                            "raw_value": str(item.value),
                            "value": "<form action='javascript:void(0);' onsubmit='update(this);'><input type='hidden' name='key' value='%s'><input title='Hit enter to apply changes to your local session' type='text' name='value' value='%s'></form>" % (str(item.key), str(item.value))})

    last_action = datetime.datetime.now().isoformat()
    action_list = dasmon.view_util.get_latest_updates(instrument_id,
                                                      message_channel=settings.SYSTEM_STATUS_PREFIX+'postprocessing')
    if len(action_list)>0:
        last_action = action_list[len(action_list)-1]['timestamp']

    # Breadcrumbs
    breadcrumbs =  "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (reverse('report.views.instrument_summary',args=[instrument]), instrument)
    breadcrumbs += " &rsaquo; configuration"

    template_values = {'instrument': instrument.upper(),
                       'helpline': settings.HELPLINE_EMAIL,
                       'params_list': params_list,
                       'action_list': action_list ,
                       'last_action_time': last_action,
                       'breadcrumbs': breadcrumbs}
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = dasmon.view_util.fill_template_values(request, **template_values)
    return render_to_response('reduction/configuration.html',
                              template_values)


@csrf_exempt
@users.view_util.login_or_local_required_401
def configuration_change(request, instrument):
    """
        AJAX call to update the reduction parameters for an instrument.
        
        @param request: request object
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    if 'data' in request.POST:
        template_data = json.loads(request.POST['data'])
        template_dict = {}
        for item in template_data:
            try:
                template_dict[item['key']] = item['value']
                props = ReductionProperty.objects.filter(instrument=instrument_id, key=item['key'])
                if len(props)==1:
                    if not props[0].value == item['value']:
                        props[0].value = item['value']
                        props[0].save()
                        modif = PropertyModification(property=props[0], 
                                                     value=props[0].value,
                                                     user=request.user)
                        modif.save()
                elif len(props)>1:
                    logging.error("config_change: more than one property named %s" % item['key'])
                else:
                    logging.error("config_change: could not find %s" % item['key'])
            except:
                logging.error("config_change: %s" % sys.exc_value)
        
        # Check whether the user wants to install the default script
        use_default = False
        if 'use_default' in request.POST:
            try:
                use_default = int(request.POST['use_default'])==1
            except:
                logging.error("Error parsing use_default parameter: %s" % sys.exc_value)
        # Send ActiveMQ request
        try:
            dasmon.view_util.add_status_entry(instrument_id,
                                              settings.SYSTEM_STATUS_PREFIX+'postprocessing',
                                              "Script requested by %s" % request.user)
            data_dict = {"instrument": instrument.upper(),
                         "use_default": use_default,
                         "template_data": template_dict,
                         "information": "Requested by %s" % str(request.user)}
            data = json.dumps(data_dict)
            reporting_app.view_util.send_activemq_message(settings.REDUCTION_SCRIPT_CREATION_QUEUE, data)
            logging.info("Reduction script requested: %s" % str(data))
        except:
            logging.error("Error sending AMQ script request: %s" % sys.exc_value)
            return HttpResponse("Error processing request", status=500)
            
    data_dict = {}
    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response

@users.view_util.login_or_local_required_401
#@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def configuration_update(request, instrument):
    """
        AJAX call that returns an updated list of recent actions taken
        on the reduction script for the specified instrument.
        
        @param request: request object
        @param instrument: instrument name
    """
    last_action = request.GET.get('since', '0')
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    action_list = []
    if last_action is not '0':
        start_time = dateparse.parse_datetime(last_action)
        start_time = timezone.make_aware(start_time, timezone.utc)
        action_list = dasmon.view_util.get_latest_updates(instrument_id,
                                                          message_channel=settings.SYSTEM_STATUS_PREFIX+'postprocessing',
                                                          start_time=start_time)
    data_dict = {'last_action_time': last_action, 'refresh_needed': '0'}
    if len(action_list)>0:
        data_dict['last_action_time'] = action_list[len(action_list)-1]['timestamp']
        data_dict['refresh_needed'] = '1'
    data_dict['actions'] = action_list
    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response