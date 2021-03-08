"""
    Live PV monitoring
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import dateformat, timezone
from django.conf import settings
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_cookie
from report.models import Instrument

import json
from . import view_util
import report.view_util
import users.view_util
import dasmon.view_util

@users.view_util.login_or_local_required
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users.view_util.monitor
@vary_on_cookie
def pv_monitor(request, instrument):
    """
        Display the list of latest PV values
        @param request: HTTP request object
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # DASMON Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse(settings.LANDING_VIEW),
            reverse('report:instrument_summary', args=[instrument]), instrument.lower(), "monitor")
    template_values = {'instrument':instrument.upper(),
                       'breadcrumbs': breadcrumbs,
                       'update_url':reverse('pvmon:get_update', args=[instrument]),
                       'key_value_pairs':view_util.get_cached_variables(instrument_id, True),
                      }
    template_values = report.view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = dasmon.view_util.fill_template_values(request, **template_values)

    return render_to_response('pvmon/pv_monitor.html', template_values)


@users.view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Get last experiment and last run
    data_dict = report.view_util.get_current_status(instrument_id)

    # Update the last PV values
    data_dict['variables'] = view_util.get_cached_variables(instrument_id, monitored_only=True)
    data_dict['variables'].extend(dasmon.view_util.get_cached_variables(instrument_id, monitored_only=False))

    # Update the recording status
    localtime = timezone.now()
    df = dateformat.DateFormat(localtime)
    recording_status = {"key": "recording_status",
                        "value": dasmon.view_util.is_running(instrument_id),
                        "timestamp": df.format(settings.DATETIME_FORMAT),
                       }
    data_dict['variables'].append(recording_status)

    # Get current DAS health status
    das_status = dasmon.view_util.get_system_health()
    data_dict['das_status'] = das_status
    data_dict['live_plot_data'] = view_util.get_live_variables(request, instrument_id)

    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response
