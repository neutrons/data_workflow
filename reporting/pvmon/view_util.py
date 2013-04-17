from pvmon.models import PVName, PV, PVCache
from django.core.urlresolvers import reverse
from django.utils import simplejson, dateformat, timezone
from django.conf import settings
import datetime
import logging
import sys
import time

def get_live_variables(request, instrument_id):  
    """
        Create a data dictionary with requested live data
        @param request: HTTP request object
        @param instrument_id: Instrument object
    """  
    # Get variable update request
    live_vars = request.GET.get('vars', '')
    if len(live_vars)>0:
        live_keys=live_vars.split(',')
    else:
        return []
    
    data_dict = []
    now = time.time()
    two_hours = now-settings.PVMON_PLOT_TIME_RANGE
    for key in live_keys:
        key = key.strip()
        if len(key)==0: continue
        try:
            data_list = []
            key_id = PVName.objects.get(name=key)
            values = PV.objects.filter(instrument_id=instrument_id,
                                       name=key_id,
                                       update_time__gte=two_hours)
            # If you don't have any values for the past 2 hours, just show
            # the latest values up to 20
            if len(values)<2:
                values = PV.objects.filter(instrument_id=instrument_id,
                                           name=key_id).order_by('update_time').reverse()
                if len(values)>settings.PVMON_NUMBER_OF_OLD_PTS:
                    values = values[:settings.PVMON_NUMBER_OF_OLD_PTS]
            for v in values:
                delta_t = now-v.update_time
                data_list.append([-delta_t/60.0, v.value])
            data_dict.append([key,data_list])
        except:
            # Could not find data for this key
            logging.warning("Could not process %s: %s" % (key, sys.exc_value))
    return data_dict

def get_cached_variables(instrument_id, monitored_only=False):
    """
        Get cached PV values for a given instrument
        @param instrument_id: Instrument object
        @param monitored_only: if True, only monitored PVs are returned
    """
    # Get the PV list
    keys = PVName.objects.all().order_by("name")
    
    key_value_pairs = []
    for k in keys:
        values = PVCache.objects.filter(instrument=instrument_id, name=k)
        if len(values)>0:
            latest = values.latest("update_time")
            
            if latest.name.monitored or monitored_only is False:
                localtime = timezone.localtime(datetime.datetime.fromtimestamp(latest.update_time))
                df = dateformat.DateFormat(localtime)
                string_value = '%g' % latest.value            
    
                item = {'key': str(latest.name),
                        'value': string_value,
                        'timestamp': df.format(settings.DATETIME_FORMAT),
                        }
                key_value_pairs.append(item)

    return key_value_pairs

