"""
    Utilities for reduction configuration views
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django.conf import settings
from django.core.urlresolvers import reverse
import logging
import json
from models import ReductionProperty, PropertyModification
import reporting_app.view_util
import dasmon.view_util
import urllib

def reduction_setup_url(instrument):
    """
        Return a URL for the reduction setup if it's enabled 
        for the given instrument
        @param instrument: instrument name
    """
    if instrument.lower() in settings.INSTRUMENT_REDUCTION_SETUP:
        return reverse('reduction.views.configuration', args=[instrument])
    return None

def store_property(instrument_id, key, value, user=None):
    """
        Store a reduction property
        
        @param instrument_id: Instrument object
        @param key: name of the property
        @param value: value of the property (string)
        @param user: user that created the change
    """
    props = ReductionProperty.objects.filter(instrument=instrument_id, key=key)
    changed_prop = None
    if len(props)==1:
        if not props[0].value == value:
            props[0].value = value
            props[0].save()
            changed_prop = props[0]
    elif len(props)>1:
        logging.error("store_property: more than one property named %s" % key)
    else:
        changed_prop = ReductionProperty(instrument=instrument_id, key=str(key), value=str(value))
        changed_prop.save()
    if user is not None and changed_prop is not None:
        modif = PropertyModification(property=changed_prop, 
                                     value=value,
                                     user=user)
        modif.save()

def send_template_request(instrument_id, template_dict, user='unknown'):
    """
        Send an ActiveMQ message to request a new script
        
        @param instrument_id: Instrument object
        @param template_dict: dictionary of peroperties
        @param user: user that created the change
    """
    use_default = False
    if 'use_default' in template_dict:
        use_default = template_dict['use_default']
        
    encoded_dict = {}
    for key, value in template_dict.items():
        if isinstance(value, basestring):
            encoded_dict[key] = urllib.quote_plus(value)
        else:
            encoded_dict[key] = value

    # Send ActiveMQ request
    dasmon.view_util.add_status_entry(instrument_id,
                                      settings.SYSTEM_STATUS_PREFIX+'postprocessing',
                                      "Script requested by %s" % user)
    
    data_dict = {"instrument": str(instrument_id).upper(),
                 "use_default": use_default,
                 "template_data": encoded_dict,
                 "information": "Requested by %s" % user}
    data = json.dumps(data_dict)
    reporting_app.view_util.send_activemq_message(settings.REDUCTION_SCRIPT_CREATION_QUEUE, data)
    logging.info("Reduction script requested: %s" % str(data))
