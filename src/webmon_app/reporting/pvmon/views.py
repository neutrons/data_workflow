"""
    Live PV monitoring
"""

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone, formats
from django.conf import settings
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_cookie
from reporting.report.models import Instrument

import json
from . import view_util
import reporting.report.view_util as report_view_util
import reporting.users.view_util as users_view_util
import reporting.dasmon.view_util as dasmon_view_util


@users_view_util.login_or_local_required
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users_view_util.monitor
@vary_on_cookie
def pv_monitor(request, instrument):
    """
    Display the list of latest PV values

    :param request: HTTP request object
    :param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # DASMON Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (
        reverse(settings.LANDING_VIEW),
        reverse("report:instrument_summary", args=[instrument]),
        instrument.lower(),
        "monitor",
    )
    template_values = {
        "instrument": instrument.upper(),
        "breadcrumbs": breadcrumbs,
        "update_url": reverse("pvmon:get_update", args=[instrument]),
        "key_value_pairs": view_util.get_cached_variables(instrument_id, True),
    }
    template_values = report_view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    template_values = dasmon_view_util.fill_template_values(request, **template_values)

    return render(request, "pvmon/pv_monitor.html", template_values)


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_update(request, instrument):
    """
    Ajax call to get updates behind the scenes

    :param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Get last experiment and last run
    data_dict = report_view_util.get_current_status(instrument_id)

    # Update the last PV values
    data_dict["variables"] = view_util.get_cached_variables(instrument_id, monitored_only=True)
    data_dict["variables"].extend(dasmon_view_util.get_cached_variables(instrument_id, monitored_only=False))

    # Update the recording status
    localtime = timezone.now()
    recording_status = {
        "key": "recording_status",
        "value": dasmon_view_util.is_running(instrument_id),
        "timestamp": formats.localize(localtime),
    }
    data_dict["variables"].append(recording_status)

    # Get current DAS health status
    das_status = dasmon_view_util.get_system_health()
    data_dict["das_status"] = das_status
    data_dict["live_plot_data"] = view_util.get_live_variables(request, instrument_id)

    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response["Connection"] = "close"
    return response
