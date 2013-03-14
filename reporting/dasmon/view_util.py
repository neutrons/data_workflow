from report.models import Instrument
from dasmon.models import Parameter, StatusVariable, StatusCache
from django.shortcuts import get_object_or_404
import logging
import sys

def get_latest(instrument_id, key_id):
    """
        Returns the latest entry for a given key on a given instrument
        @param instrument_id: Instrument object
        @param key_id: Parameter object
    """
    # First get it from the cache
    try:
        last_value = StatusCache.objects.filter(instrument_id=instrument_id,
                                                key_id=key_id).latest('timestamp')
    except:
        # If that didn't work, get it from the table of values
        last_value = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                   key_id=key_id).latest('timestamp')
        
        # Put the latest value in the cache so we don't have to go through this again
        cached = StatusCache(instrument_id=last_value.instrument_id,
                             key_id=last_value.key_id,
                             value=last_value.value,
                             timestamp=last_value.timestamp)
        cached.save()
        
    return last_value

    
def is_running(instrument_id):
    """
        Returns a string with the running status for a
        given instrument
        @param instrument_id: Instrument object
    """
    try:
        key_id = Parameter.objects.get(name="recording")
        last_value = get_latest(instrument_id, key_id)
        is_recording = last_value.value.lower()=="true"

        key_id = Parameter.objects.get(name="paused")
        last_value = get_latest(instrument_id, key_id)
        is_paused = last_value.value.lower()=="true"
            
        if is_recording:
            if is_paused:
                return "Paused"
            else:
                return "Recording"
        else:
            return "Stopped"
    except:
        pass
    return "Unknown"

    
    
def get_run_status(**template_args):
    """
        Fill a template dictionary with run information
    """
    def _find_and_fill(dasmon_name):
        _value = "Unknown"
        try:
            key_id = Parameter.objects.get(name=dasmon_name)
            last_value = get_latest(instrument_id, key_id)
            _value = last_value.value
        except:
            pass
        template_args[dasmon_name] = _value
    
    if "instrument" not in template_args:
        return template_args
    
    instr = template_args["instrument"].lower()
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instr)
    
    # Get all available parameters
    keys = Parameter.objects.all().order_by('name')
    
    # Look information to pull out
    _find_and_fill("run_number")
    _find_and_fill("count_rate")
    _find_and_fill("proposal_id")
    _find_and_fill("run_title")
    
    # Are we recording or not?
    template_args["recording_status"] = is_running(instrument_id)

    return template_args

def get_live_variables(request, instrument_id):  
    """
        Create a data dictionary with requested live data
    """  
    # Get variable update request
    live_vars = request.GET.get('vars', '')
    if len(live_vars)>0:
        live_keys=live_vars.split(',')
    else:
        return []
    
    data_dict = []
    for key in live_keys:
        key = key.strip()
        if len(key)==0: continue
        try:
            data_list = []
            key_id = Parameter.objects.get(name=key)
            values = StatusVariable.objects.filter(instrument_id=instrument_id,
                                                   key_id=key_id).order_by('timestamp').reverse()
            values = values[:120]
            for v in values:
                delta_t = values[0].timestamp-v.timestamp
                data_list.append([-delta_t.seconds, v.value])
            data_dict.append([key,data_list])
        except:
            # Could not find data for this key
            logging.warning("Could not process %s: %s" % (key, sys.exc_value))
    return data_dict
