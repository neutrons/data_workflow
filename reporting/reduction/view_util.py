"""
    Utilities for reduction configuration views
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django.conf import settings
import logging
import json
from models import ReductionProperty, PropertyModification
import reporting_app.view_util
import dasmon.view_util
import urllib

def store_property(instrument_id, key, value, user=None):
    """
        Store a reduction property
        
        @param instrument_id: Instrument object
        @param key: name of the property
        @param value: value of the property (string)
        @param user: user that created the change
    """
    props = ReductionProperty.objects.filter(instrument=instrument_id, key=key)
    if len(props)==1:
        if not props[0].value == value:
            props[0].value = value
            props[0].save()
            if user is not None:
                modif = PropertyModification(property=props[0], 
                                             value=props[0].value,
                                             user=user)
                modif.save()
    elif len(props)>1:
        logging.error("forms.ReductionConfigurationSEQForm: more than one property named %s" % key)
    else:
        logging.error("forms.ReductionConfigurationSEQForm: could not find %s" % key)

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
