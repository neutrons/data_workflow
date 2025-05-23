# pylint: disable=invalid-name, line-too-long, too-many-locals, bare-except
"""
Live monitoring
"""
import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone, formats
from django.conf import settings
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_cookie
from django.template import loader
from django.contrib.auth.decorators import login_required
from django import forms

from reporting.report.models import Instrument
import reporting.report.view_util as report_view_util
from reporting.users.models import SiteNotification
import reporting.users.view_util as users_view_util
from reporting.dasmon.models import ActiveInstrument, Signal, UserNotification
from . import view_util


@users_view_util.login_or_local_required
@cache_page(settings.SLOW_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users_view_util.monitor
@vary_on_cookie
def dashboard(request):
    """
    Dashboard view showing available instruments
    """
    # Get the system health status
    global_status_url = reverse(settings.LANDING_VIEW, args=[])
    instrument_data = view_util.get_instrument_status_summary()
    template_values = {
        "instruments": instrument_data,
        "data": view_util.get_dashboard_data(),
        "breadcrumbs": "<a href='%s'>home</a> &rsaquo; dashboard" % global_status_url,
        "postprocess_status": view_util.get_system_health(),
        "update_url": reverse("dasmon:dashboard_update") + "?plots",
        "central_services_url": reverse("dasmon:diagnostics", args=["common"]),
    }
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "dasmon/dashboard.html", template_values)


@users_view_util.login_or_local_required
@cache_page(settings.SLOW_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users_view_util.monitor
@vary_on_cookie
def dashboard_simple(request):
    """
    Dashboard view showing available instruments
    """
    # Get the system health status
    global_status_url = reverse(settings.LANDING_VIEW, args=[])
    instrument_data = view_util.get_instrument_status_summary()
    template_values = {
        "instruments": instrument_data,
        "breadcrumbs": "<a href='%s'>home</a> &rsaquo; dashboard" % global_status_url,
        "postprocess_status": view_util.get_system_health(),
        "update_url": reverse("dasmon:dashboard_update"),
        "central_services_url": reverse("dasmon:diagnostics", args=["common"]),
    }
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "dasmon/dashboard_simple.html", template_values)


@users_view_util.login_or_local_required_401
@cache_page(settings.SLOW_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
def dashboard_update(request):
    """
    Response to AJAX call to get updated health info for all instruments
    """
    # Get the system health status
    data_dict = {
        "instruments": view_util.get_instrument_status_summary(),
        "postprocess_status": view_util.get_system_health(),
    }
    if "plots" in request.GET:
        data_dict["instrument_rates"] = view_util.get_dashboard_data()
    return JsonResponse(data_dict)


@users_view_util.login_or_local_required
@cache_page(settings.SLOW_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users_view_util.monitor
@vary_on_cookie
def expert_status(request):
    """
    Internal status for development team
    """
    # Get the system health status
    global_status_url = reverse(settings.LANDING_VIEW, args=[])

    template_values = {
        "instruments": view_util.get_instrument_status_summary(True),
        "breadcrumbs": "<a href='%s'>home</a> &rsaquo; dashboard" % global_status_url,
        "postprocess_status": view_util.get_system_health(),
        "update_url": reverse("dasmon:dashboard_update"),
        "central_services_url": reverse("dasmon:diagnostics", args=["common"]),
    }
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "dasmon/expert_status.html", template_values)


@users_view_util.login_or_local_required
@cache_page(settings.SLOW_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users_view_util.monitor
@vary_on_cookie
def run_summary(request):
    """
    Dashboard view showing available instruments
    """
    global_status_url = reverse(settings.LANDING_VIEW, args=[])
    base_instr_url = reverse("dasmon:live_monitor", args=["aaaa"])
    base_instr_url = base_instr_url.replace("/aaaa", "")
    base_run_url = reverse("report:instrument_summary", args=["aaaa"])
    base_run_url = base_run_url.replace("/aaaa", "")

    template_values = {
        "run_list_url": reverse("dasmon:run_summary_update"),
        "base_instrument_url": base_instr_url,
        "base_run_url": base_run_url,
        "breadcrumbs": "<a href='%s'>home</a> &rsaquo; dashboard" % global_status_url,
    }
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "dasmon/run_summary.html", template_values)


@users_view_util.login_or_local_required_401
def run_summary_update(request):

    limit = int(request.GET.get("length", 10))
    offset = int(request.GET.get("start", 0))
    draw = int(request.GET.get("draw", 1))

    instrument_search = request.GET.get("columns[0][search][value]", "")
    run_search = request.GET.get("columns[1][search][value]", "")
    date_search = request.GET.get("columns[2][search][value]", "")
    status_search = request.GET.get("columns[3][search][value]", "")

    run_list, count, filtered_count = view_util.get_run_list_newest(
        offset, limit, instrument_search, run_search, date_search, status_search
    )
    data = {}
    data["data"] = report_view_util.get_run_list_dict(run_list)
    data["recordsTotal"] = count
    data["recordsFiltered"] = filtered_count
    data["draw"] = draw

    return JsonResponse(data)


@users_view_util.login_or_local_required
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users_view_util.monitor
@vary_on_cookie
def live_monitor(request, instrument):
    """
    Display the list of current DASMON status

    :param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Update URL
    update_url = reverse("dasmon:get_update", args=[instrument])
    pv_url = reverse("pvmon:get_update", args=[instrument])

    breadcrumbs = view_util.get_monitor_breadcrumbs(instrument_id)
    template_values = {
        "instrument": instrument.upper(),
        "breadcrumbs": breadcrumbs,
        "update_url": update_url,
        "pv_url": pv_url,
        "key_value_pairs": view_util.get_cached_variables(instrument_id, monitored_only=True),
    }
    template_values = report_view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    template_values = view_util.fill_template_values(request, **template_values)

    template_values["signals_url"] = reverse("dasmon:get_signal_table", args=[instrument])

    return render(request, "dasmon/live_monitor.html", template_values)


@users_view_util.login_or_local_required
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users_view_util.monitor
@vary_on_cookie
def live_runs(request, instrument):
    """
    Display the list of latest runs

    :param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Update URL
    update_url = reverse("dasmon:get_update", args=[instrument])

    breadcrumbs = view_util.get_monitor_breadcrumbs(instrument_id)
    template_values = {
        "instrument": instrument.upper(),
        "breadcrumbs": breadcrumbs,
        "update_url": update_url,
    }
    template_values = report_view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    template_values = view_util.fill_template_values(request, **template_values)

    return render(request, "dasmon/live_runs.html", template_values)


@users_view_util.login_or_local_required
@users_view_util.monitor
def user_help(request):
    """
    Help request
    """
    global_status_url = reverse(settings.LANDING_VIEW, args=[])
    hysa_live_monitor_url = reverse("dasmon:live_monitor", args=["hysa"])
    hysa_live_runs_url = reverse("dasmon:live_runs", args=["hysa"])

    breadcrumbs = "<a href='%s'>home</a> &rsaquo; help" % global_status_url

    template_values = {
        "global_status_url": global_status_url,
        "hysa_live_monitor_url": hysa_live_monitor_url,
        "hysa_live_runs_url": hysa_live_runs_url,
        "breadcrumbs": breadcrumbs,
    }
    template_values = users_view_util.fill_template_values(request, **template_values)

    return render(request, "dasmon/help.html", template_values)


@users_view_util.login_or_local_required
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@users_view_util.monitor
@vary_on_cookie
def diagnostics(request, instrument):
    """
    Diagnose the health of an instrument

    :param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Workflow Manager
    wf_diag = view_util.workflow_diagnostics()
    # Post-processing
    red_diag = view_util.postprocessing_diagnostics()
    # reduction queue size
    red_queue_size = report_view_util.reduction_queue_sizes()

    breadcrumbs = view_util.get_monitor_breadcrumbs(instrument_id, "diagnostics")
    template_values = {
        "instrument": instrument.upper(),
        "breadcrumbs": breadcrumbs,
    }
    template_values = report_view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    template_values = view_util.fill_template_values(request, **template_values)

    actions = []
    if ActiveInstrument.objects.is_adara(instrument_id):
        # DASMON
        dasmon_diag = view_util.dasmon_diagnostics(instrument_id)
        template_values["dasmon_diagnostics"] = dasmon_diag
        # PVStreamer
        if ActiveInstrument.objects.has_pvstreamer(instrument_id):
            template_values["pv_diagnostics"] = view_util.pvstreamer_diagnostics(instrument_id)
        # PVSD
        if ActiveInstrument.objects.has_pvsd(instrument_id):
            template_values["pvsd_diagnostics"] = view_util.pvstreamer_diagnostics(instrument_id, process="pvsd")
        # Actions messages
        if dasmon_diag["dasmon_listener_warning"] and wf_diag["dasmon_listener_warning"]:  # noqa: W503
            actions.append(
                "Multiple heartbeat message failures: ask Linux Support to restart dasmon_listener before proceeding"
            )

    template_values["wf_diagnostics"] = wf_diag
    template_values["post_diagnostics"] = red_diag
    template_values["reduction_queue_size"] = red_queue_size
    template_values["action_messages"] = actions

    notices = []
    for item in SiteNotification.objects.filter(is_active=True):
        notices.append(item.message)
    if len(notices) > 0:
        template_values["user_alert"] = notices

    return render(request, "dasmon/diagnostics.html", template_values)


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
def get_update(request, instrument):

    limit = int(request.GET.get("length", 10))
    offset = int(request.GET.get("start", 0))
    draw = int(request.GET.get("draw", 1))

    run_search = request.GET.get("columns[0][search][value]", "")
    date_search = request.GET.get("columns[1][search][value]", "")
    status_search = request.GET.get("columns[2][search][value]", "")

    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Get last experiment and last run
    data_dict = report_view_util.get_current_status(instrument_id)
    data_dict["variables"] = view_util.get_cached_variables(instrument_id, monitored_only=False)

    localtime = timezone.now()
    recording_status = {
        "key": "recording_status",
        "value": view_util.is_running(instrument_id),
        "timestamp": formats.localize(localtime),
    }
    data_dict["variables"].append(recording_status)

    # Get current DAS health status
    das_status = view_util.get_system_health(instrument_id)
    data_dict["das_status"] = das_status
    data_dict["live_plot_data"] = view_util.get_live_variables(request, instrument_id)

    run_list, count, filtered_count = view_util.get_run_list_instrument_newest(
        instrument_id, offset, limit, run_search, date_search, status_search
    )
    data_dict["data"] = report_view_util.get_run_list_dict(run_list)
    data_dict["recordsTotal"] = count
    data_dict["recordsFiltered"] = filtered_count
    data_dict["draw"] = draw

    return JsonResponse(data_dict)


@users_view_util.login_or_local_required_401
def summary_update(request):
    """
    Response to AJAX call to get updated health info for all instruments
    """
    # Get the system health status
    data_dict = {
        "instruments": view_util.get_instrument_status_summary(),
        "postprocess_status": view_util.get_system_health(),
    }
    return JsonResponse(data_dict)


@users_view_util.login_or_local_required_401
def get_signal_table(request, instrument):
    """
    Ajax call to get the signal table

    Note: Since users can interact with this table, we are not caching it.
    That avoids seeing cleared entries momentarily reappearing in the case
    where the page requests a refresh while the cache hasn't yet been updated.
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    t = loader.get_template("dasmon/signal_table.html")
    template_values = {"signals": view_util.get_signals(instrument_id)}
    template_values["is_instrument_staff"] = users_view_util.is_instrument_staff(request, instrument_id)
    resp = t.render(template_values)
    response = HttpResponse(resp, content_type="text/html")
    response["Connection"] = "close"
    response["Content-Length"] = len(response.content)
    return response


@users_view_util.login_or_local_required_401
@users_view_util.monitor
def acknowledge_signal(request, instrument, sig_id):
    """
    Acknowledge a signal and remove it from the DB

    :param request: request obect
    :param instrument: instrument name
    :param sig_id: signal ID
    """
    try:
        sig_object = get_object_or_404(Signal, id=sig_id)
        sig_object.delete()
    except:  # noqa: E722
        logging.exception("ACK signal %s/%s:", instrument, sig_id)
    return HttpResponse()


@login_required
def notifications(request):
    """
    Let an instrument team member register for a DASMON signal
    """
    instrument_list = view_util.get_instruments_for_user(request)

    class NotificationForm(forms.Form):
        """
        Form for notification registration
        """

        email = forms.EmailField(required=False, initial="")
        register = forms.BooleanField(required=False, initial=False)
        instruments = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            options = ()
            for i in instrument_list:
                options += ((i, i),)
            self.fields["instruments"] = forms.MultipleChoiceField(
                widget=forms.CheckboxSelectMultiple, choices=options
            )

    # Process request
    alert_list = []
    if request.method == "POST":
        options_form = NotificationForm(request.POST)
        if options_form.is_valid():
            email_address = options_form.cleaned_data["email"]
            registered = options_form.cleaned_data["register"]
            instruments = options_form.cleaned_data["instruments"]
            try:
                user_options_list = UserNotification.objects.filter(user_id=request.user.id)
                if len(user_options_list) == 0:
                    user_options = UserNotification(
                        user_id=request.user.id,
                        email=email_address,
                        registered=registered,
                    )
                    user_options.save()
                else:
                    user_options = user_options_list[0]
                    user_options.email = email_address
                    user_options.registered = registered
                # Add the instruments
                user_options.instruments.clear()
                for item in instruments:
                    try:
                        inst_entry = Instrument.objects.get(name=item.lower())
                        user_options.instruments.add(inst_entry)
                        user_options.save()
                    except:  # noqa: E722
                        alert_list.append("Could not find instrument %s" % item)
                        logging.exception("Notification registration failed:")
                alert_list.append("Your changes have been saved.")

            except:  # noqa: E722
                alert_list.append("There was a problem processing your request.")
                logging.exception("Error processing notification settings:")
        else:
            alert_list.append("Your form is invalid. Please modify your entries and re-submit.")
            logging.error("Invalid form %s", options_form.errors)
    else:
        params_dict = {}
        try:
            user_options = UserNotification.objects.get(user_id=request.user.id)
            params_dict["email"] = user_options.email
            params_dict["register"] = user_options.registered
            params_dict["instruments"] = []
            for item in user_options.instruments.all():
                params_dict["instruments"].append(item.name.upper())
        except:  # noqa: E722
            # No entry found for this user. Use a blank form.
            pass
        options_form = NotificationForm(initial=params_dict)

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; notifications"

    template_values = {
        "helpline": settings.HELPLINE_EMAIL,
        "options_form": options_form,
        "user_alert": alert_list,
        "breadcrumbs": breadcrumbs,
    }
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "dasmon/notifications.html", template_values)
