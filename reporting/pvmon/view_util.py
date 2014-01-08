from pvmon.models import PVName, PV, PVCache
from django.utils import dateformat, timezone
from django.conf import settings
import datetime
import logging
import sys
import time
import math

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
    plot_timeframe = request.GET.get('time', settings.PVMON_PLOT_TIME_RANGE)
    try:
        plot_timeframe = int(plot_timeframe)
    except:
        logging.warning("Bad time period request: %s" % str(plot_timeframe))
        plot_timeframe = settings.PVMON_PLOT_TIME_RANGE

    
    data_dict = []
    now = time.time()
    two_hours = now-plot_timeframe
    for key in live_keys:
        key = key.strip()
        if len(key)==0: continue
        try:
            data_list = []
            key_id = PVName.objects.get(name=key)
            values = PV.objects.filter(instrument_id=instrument_id,
                                       name=key_id,
                                       update_time__gte=two_hours)
            if len(values)>0:
                values = values.order_by('update_time').reverse()
            # If you don't have any values for the past 2 hours, just show
            # the latest values up to 20
            if len(values)<2:
                values = PV.objects.filter(instrument_id=instrument_id,
                                           name=key_id)
                if len(values)>0:
                    values = values.order_by('update_time').reverse()
                else:
                    latest_entry = PVCache.objects.filter(instrument=instrument_id, name=key_id)
                    if len(latest_entry)>0:
                        latest_entry = latest_entry.latest("update_time")
                        delta_t = now-latest_entry.update_time
                        data_dict.append([key,[[-delta_t/60.0, latest_entry.value], [0, latest_entry.value]]])
                    else:
                        data_dict.append([key,[]])
                    continue
                if len(values)>settings.PVMON_NUMBER_OF_OLD_PTS:
                    values = values[:settings.PVMON_NUMBER_OF_OLD_PTS]

            # Average out points every two minutes when plotting a long period of time
            if now-values[len(values)-1].update_time>2*60*60:
                range_t = now-values[len(values)-1].update_time
                range_minutes = int(math.floor(range_t/120))+1
                data_values = range_minutes*[0]
                data_counts = range_minutes*[0]
                for v in values:
                    delta_t = now-v.update_time
                    i_bin = int(math.floor(delta_t/120))
                    data_counts[i_bin] += 1.0
                    data_values[i_bin] += float(v.value)
                for i in range(range_minutes):
                    if data_counts[i]>0:
                        data_values[i] /= data_counts[i]
                    data_list.append([-i*2.0, data_values[i]])                
            else:
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
    values = PVCache.objects.filter(instrument=instrument_id)
    if len(values)>0:
        values = values.order_by("name__name")
    
    key_value_pairs = []
    for kvp in values:
        if kvp.name.monitored or monitored_only is False:
            localtime = datetime.datetime.fromtimestamp(kvp.update_time).replace(tzinfo=timezone.utc)
            df = dateformat.DateFormat(localtime)
            string_value = '%g' % kvp.value            

            item = {'key': str(kvp.name),
                    'value': string_value,
                    'timestamp': df.format(settings.DATETIME_FORMAT),
                    }
            key_value_pairs.append(item)

    return key_value_pairs

