# pylint: disable=too-many-branches, line-too-long, too-many-locals, too-many-statements, bare-except, invalid-name
"""
    Utilities to compile the PVs stored in the web monitor DB.

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
import sys
from pvmon.models import PVName, PV, PVCache, PVStringCache
from django.utils import dateformat, timezone
from django.conf import settings
import datetime
import logging
import time


def get_live_variables(request, instrument_id, key_id=None):
    """
        Create a data dictionary with requested live data
        @param request: HTTP request object
        @param instrument_id: Instrument object
        @param key_id: key to return data for, if request is None
    """
    # Get variable update request
    if request is not None:
        live_vars = request.GET.get('vars', '')
        if len(live_vars) > 0:
            live_keys_str = live_vars.split(',')
            live_keys = []
            for key in live_keys_str:
                key = key.strip()
                if len(key) == 0:
                    continue
                # First try exact match, if no match than try case-insensitive exact match
                key_ids = PVName.objects.filter(name__exact=key)
                if len(key_ids) == 0:
                    key_ids = PVName.objects.filter(name__iexact=key)
                if len(key_ids) > 0:
                    key_id = key_ids[0]
                else:
                    logging.error("Error finding %s", key)
                    return []
                live_keys.append(key_id)
        else:
            return []
        plot_timeframe = request.GET.get('time', settings.PVMON_PLOT_TIME_RANGE)
    else:
        if key_id is None:
            return []
        live_keys = [key_id]
        plot_timeframe = settings.DASMON_PLOT_TIME_RANGE
    try:
        plot_timeframe = int(plot_timeframe)
    except:
        logging.warning("Bad time period request: %s", str(plot_timeframe))
        plot_timeframe = settings.PVMON_PLOT_TIME_RANGE

    data_dict = []
    now = time.time()
    two_hours = now - plot_timeframe
    for key_id in live_keys:
        key = str(key_id.name)
        try:
            data_list = []
            values = PV.objects.filter(instrument_id=instrument_id,
                                       name=key_id,
                                       update_time__gte=two_hours)
            if len(values) > 0:
                values = values.order_by('update_time').reverse()
            # If you don't have any values for the past 2 hours, just show
            # the latest values up to 20
            if len(values) < 2:
                values = PV.objects.filter(instrument_id=instrument_id,
                                           name=key_id)
                if len(values) > 0:
                    values = values.order_by('update_time').reverse()
                else:
                    latest_entry = PVCache.objects.filter(instrument=instrument_id, name=key_id)
                    if len(latest_entry) > 0:
                        latest_entry = latest_entry.latest("update_time")
                        delta_t = now - latest_entry.update_time
                        data_dict.append([key, [[-delta_t / 60.0, latest_entry.value], [0, latest_entry.value]]])
                    else:
                        data_dict.append([key, []])
                    continue
                if len(values) > settings.PVMON_NUMBER_OF_OLD_PTS:
                    values = values[:settings.PVMON_NUMBER_OF_OLD_PTS]

            for v in values:
                delta_t = now - v.update_time
                data_list.append([-delta_t / 60.0, v.value])
            data_dict.append([key, data_list])
        except:
            # Could not find data for this key
            logging.warning("Could not process %s: %s", key, str(sys.exc_info()[1]))
    return data_dict


def get_cached_variables(instrument_id, monitored_only=False):
    """
        Get cached PV values for a given instrument
        @param instrument_id: Instrument object
        @param monitored_only: if True, only monitored PVs are returned
    """
    def _process_pvs(queryset):
        """
            Process PVs
        """
        for kvp in queryset:
            if kvp.name.monitored or monitored_only is False:
                localtime = datetime.datetime.fromtimestamp(kvp.update_time).replace(tzinfo=timezone.utc)
                df = dateformat.DateFormat(localtime)
                if isinstance(kvp.value, (int, float)):
                    string_value = '%g' % kvp.value
                else:
                    string_value = '%s' % kvp.value

                item = {'key': str(kvp.name),
                        'value': string_value,
                        'timestamp': df.format(settings.DATETIME_FORMAT),
                        }
                key_value_pairs.append(item)

    key_value_pairs = []
    values = PVCache.objects.filter(instrument=instrument_id)
    if len(values) > 0:
        values = values.order_by("name__name")
    _process_pvs(values)

    values = PVStringCache.objects.filter(instrument=instrument_id)
    if len(values) > 0:
        values = values.order_by("name__name")
    _process_pvs(values)

    return key_value_pairs
