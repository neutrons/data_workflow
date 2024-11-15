# pylint: disable=invalid-name, line-too-long, too-many-locals, bare-except, unused-argument
"""
    Report views

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014-2015 Oak Ridge National Laboratory
"""
import sys
import logging
import json
import datetime
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone, formats
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_cookie
from django.conf import settings
from django.contrib.auth.decorators import login_required

from reporting.dasmon.models import ActiveInstrument
from reporting.report.models import DataRun, IPTS, Instrument, Error, RunStatus
from reporting.report.catalog import get_run_info
from reporting.report.forms import ProcessingForm
from . import view_util
import reporting.users.view_util as users_view_util
import reporting.dasmon.view_util as dasmon_view_util
import reporting.reporting_app.view_util as reporting_view_util


@login_required
def processing_admin(request):
    """
    Form to let admins easily reprocess parts of the workflow
    """
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; processing" % reverse(settings.LANDING_VIEW)
    template_values = {"breadcrumbs": breadcrumbs, "notes": ""}
    template_values = users_view_util.fill_template_values(request, **template_values)

    instruments = [str(i) for i in Instrument.objects.all().order_by("name") if ActiveInstrument.objects.is_alive(i)]
    instrument = instruments[0]

    if request.method == "POST":
        # Get instrument
        if "instrument" in request.POST:
            instrument = request.POST["instrument"]

        processing_form = ProcessingForm(request.POST)
        if request.POST.get("button_choice", "none") == "find":
            instrument_id = get_object_or_404(Instrument, name=instrument.lower())
            skipped_runs = view_util.find_skipped_runs(instrument_id)
            template_values["notes"] = "Missing runs: %s" % str(skipped_runs)

        elif processing_form.is_valid():
            output = processing_form.process()
            template_values["notes"] = output["report"]

            # Submit task and append success outcome to notes.
            if "runs" in output and "instrument" in output and "task" in output and output["task"] is not None:
                submission_errors = ""
                for run_obj in output["runs"]:
                    try:
                        is_complete = output.get("is_complete", False)
                        view_util.send_processing_request(
                            output["instrument"],
                            run_obj,
                            user=request.user,
                            destination=output["task"],
                            is_complete=is_complete,
                        )
                    except:  # noqa: E722
                        submission_errors += "%s run %s could not be submitted: %s<br>" % (
                            str(run_obj.instrument_id),
                            str(run_obj.run_number),
                            sys.exc_info()[1],
                        )
                        logging.exception("")
                template_values["notes"] += submission_errors
                if len(submission_errors) == 0:
                    template_values["notes"] += "<b>All tasks were submitted</b><br>"
    else:
        # Get instrument
        if "instrument" in request.GET:
            instrument = request.GET["instrument"]

        processing_form = ProcessingForm()
        processing_form.set_initial(request.GET)

    # Get list of available experiments
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    ipts = [str(i) for i in IPTS.objects.filter(instruments=instrument_id)]

    template_values["form"] = processing_form
    template_values["experiment_list"] = ipts

    return render(request, "report/processing_admin.html", template_values)


@users_view_util.login_or_local_required
def summary(request):
    """
    List of available instruments
    """
    instruments = Instrument.objects.all().order_by("name")
    # Get base URL
    base_url = reverse("report:instrument_summary", args=["aaaa"])
    base_url = base_url.replace("/aaaa", "")
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; summary" % reverse(settings.LANDING_VIEW)

    # Number of runs as a function of time
    max_date = datetime.datetime.now().replace(day=1).replace(tzinfo=timezone.get_current_timezone())
    epoch = datetime.datetime(1970, 1, 1).replace(tzinfo=timezone.get_current_timezone())
    adara_start = datetime.datetime(2012, 10, 1).replace(tzinfo=timezone.get_current_timezone())
    today = datetime.datetime.today().replace(tzinfo=timezone.get_current_timezone())
    # Fill in the partial data for the current month
    number_of_runs = DataRun.objects.filter(created_on__gte=max_date).count()
    run_rate = []
    run_summary = [
        {
            "min_date": max_date,
            "max_date": datetime.datetime.today(),
            "number_of_runs": number_of_runs,
        }
    ]
    run_rate.append([1000 * int((today - epoch).total_seconds()), number_of_runs])
    while True:
        # Make sure we don't display zeros for the period before
        # the system was installed
        if max_date < adara_start:
            break
        # Start date
        month = max_date.month - 1
        if month <= 0:
            min_date = max_date.replace(month=12, year=max_date.year - 1)
        else:
            min_date = max_date.replace(month=month)

        runs = DataRun.objects.filter(created_on__lt=max_date, created_on__gte=min_date)
        run_summary.append({"min_date": min_date, "max_date": max_date, "number_of_runs": len(runs)})
        run_rate.append([1000 * int((max_date - epoch).total_seconds()), len(runs)])

        # Update end date
        month = max_date.month - 1
        if month <= 0:
            max_date = max_date.replace(month=12, year=max_date.year - 1)
        else:
            max_date = max_date.replace(month=month)

    template_values = {
        "instruments": instruments,
        "run_summary": run_summary,
        "run_rate": run_rate,
        "breadcrumbs": breadcrumbs,
        "base_instrument_url": base_url,
    }
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "report/global_summary.html", template_values)


@login_required
def download_reduced_data(request, instrument, run_id):
    """
    Download reduced data from live data server

    :param request: http request object
    :param instrument: instrument name
    :param run_id: run number
    """
    html_data = view_util.get_plot_data_from_server(instrument, run_id, "html")
    ascii_data = view_util.extract_ascii_from_div(html_data)
    if ascii_data is None:
        error_msg = "No data available for %s %s" % (instrument, run_id)
        return HttpResponseNotFound(error_msg)
    ascii_data = "# %s Run %s\n# X Y dY dX\n%s" % (
        instrument.upper(),
        run_id,
        ascii_data,
    )
    response = HttpResponse(ascii_data, content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename=%s_%s.txt" % (
        instrument.upper(),
        run_id,
    )
    return response


@users_view_util.login_or_local_required
def detail(request, instrument, run_id):
    """
    Run details

    :param instrument: instrument name
    :param run_id: run number, as string
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    run_object = get_object_or_404(DataRun, instrument_id=instrument_id, run_number=run_id)

    icat_info = get_run_info(instrument, str(run_object.ipts_id), run_id)

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (
        reverse("report:instrument_summary", args=[instrument]),
        instrument,
    )
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (
        reverse("report:ipts_summary", args=[instrument, run_object.ipts_id.expt_name]),
        str(run_object.ipts_id).lower(),
    )
    breadcrumbs += " &rsaquo; run %s" % run_id
    if users_view_util.is_experiment_member(request, instrument_id, run_object.ipts_id) is False:
        template_values = {
            "instrument": instrument.upper(),
            "run_object": run_object,
            "helpline": settings.HELPLINE_EMAIL,
            "breadcrumbs": breadcrumbs,
        }
        template_values = users_view_util.fill_template_values(request, **template_values)
        template_values = dasmon_view_util.fill_template_values(request, **template_values)
        return render(request, "report/private_data.html", template_values)

    # Check whether we need a re-reduce link
    reduce_url = None
    if view_util.needs_reduction(request, run_object):
        reduce_url = "reduce"

    # Find status entries
    status_objects = RunStatus.objects.filter(run_id=run_object).order_by("created_on").reverse()

    # Look for an image of the reduction
    plot_template_dict = view_util.get_plot_template_dict(run_object, instrument, run_id)

    # Check whether this is the last known run for this instrument
    last_run_id = DataRun.objects.get_last_cached_run(instrument_id)
    if last_run_id == run_object:
        next_url = None
    else:
        try:
            DataRun.objects.get(instrument_id=instrument_id, run_number=run_object.run_number + 1)
            next_url = reverse("report:detail", args=[instrument, run_object.run_number + 1])
        except:  # noqa: E722
            next_url = None

    # Get previous run
    try:
        DataRun.objects.get(instrument_id=instrument_id, run_number=run_object.run_number - 1)
        prev_url = reverse("report:detail", args=[instrument, run_object.run_number - 1])
    except:  # noqa: E722
        prev_url = None

    template_values = {
        "instrument": instrument.upper(),
        "run_object": run_object,
        "status": status_objects,
        "breadcrumbs": breadcrumbs,
        "icat_info": icat_info,
        "reduce_url": reduce_url,
        "reduction_setup_url": reporting_view_util.reduction_setup_url(instrument),
        "prev_url": prev_url,
        "next_url": next_url,
    }
    template_values.update(plot_template_dict)
    if icat_info == {}:
        template_values["user_alert"] = ["Could not communicate with the online catalog"]
    try:
        if "data_files" not in icat_info or icat_info["data_files"] is None or len(icat_info["data_files"]) == 0:
            if view_util.is_acquisition_complete(run_object):
                template_values["no_icat_info"] = "There is no catalog information for this run yet."
            else:
                template_values["no_icat_info"] = "The final data file for this run is not yet available."

    except:  # noqa: E722
        logging.exception("Could not determine whether we have catalog info:")
        template_values["no_icat_info"] = "There is no catalog information for this run yet."
    template_values = users_view_util.fill_template_values(request, **template_values)
    template_values = dasmon_view_util.fill_template_values(request, **template_values)
    return render(request, "report/detail.html", template_values)


@login_required
def submit_for_reduction(request, instrument, run_id):
    """
    Send a run for automated reduction

    :param instrument: instrument name
    :param run_id: run number
    """
    return view_util.processing_request(request, instrument, run_id, destination="/queue/REDUCTION.REQUEST")


@login_required
def submit_for_post_processing(request, instrument, run_id):
    """
    Send a run for complete post-processing

    :param instrument: instrument name
    :param run_id: run number
    """
    return view_util.processing_request(request, instrument, run_id, destination="/queue/POSTPROCESS.DATA_READY")


@login_required
def submit_for_cataloging(request, instrument, run_id):
    """
    Send a run for cataloging

    :param instrument: instrument name
    :param run_id: run number
    """
    return view_util.processing_request(request, instrument, run_id, destination="/queue/CATALOG.REQUEST")


@users_view_util.login_or_local_required
def instrument_summary(request, instrument):
    """
    Instrument summary page

    :param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Get list of IPTS
    ipts = IPTS.objects.filter(instruments=instrument_id).order_by("created_on").reverse()
    expt_list = []
    for expt in ipts:
        localtime = timezone.localtime(expt.created_on)
        expt_list.append(
            {
                "experiment": str(
                    "<a href='%s'>%s</a>"
                    % (
                        reverse("report:ipts_summary", args=[instrument, expt.expt_name]),
                        expt.expt_name,
                    )
                ),
                "total": expt.number_of_runs(),
                "timestamp": expt.created_on.isoformat(),
                "created_on": formats.localize(localtime),
            }
        )

    # Instrument error URL
    error_url = reverse("report:live_errors", args=[instrument])

    # Update URL for live monitoring
    update_url = reverse("report:get_instrument_update", args=[instrument])

    # Get the last IPTS created so that we can properly do the live update
    if IPTS.objects.filter(instruments=instrument_id).count() > 0:
        last_expt_created = IPTS.objects.filter(instruments=instrument_id).latest("id")
    else:
        last_expt_created = None

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s" % (
        reverse(settings.LANDING_VIEW),
        instrument.lower(),
    )

    template_values = {
        "instrument": instrument.upper(),
        "expt_list": expt_list,
        "breadcrumbs": breadcrumbs,
        "error_url": error_url,
        "update_url": update_url,
        "last_expt_created": last_expt_created,
    }
    template_values = view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "report/instrument.html", template_values)


@users_view_util.login_or_local_required
def ipts_summary(request, instrument, ipts):
    """
    Experiment summary giving the list of runs

    :param instrument: instrument name
    :param ipts: experiment name
    """
    # Protect against lower-case requests
    ipts = ipts.upper()
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    # Get experiment
    ipts_id = get_object_or_404(IPTS, expt_name=ipts, instruments=instrument_id)

    # Get IPTS URL
    ipts_url = reverse("report:ipts_summary", args=[instrument, ipts])
    update_url = reverse("report:get_experiment_update", args=[instrument, ipts])

    # Get the latest run and experiment so we can determine later
    # whether the user should refresh the page
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    runs = DataRun.objects.filter(instrument_id=instrument_id, ipts_id=ipts_id).order_by("created_on")
    run_list = view_util.get_run_list_dict(runs)

    # Get the ID of the first displayed run so that we can update the
    # status of runs that are displayed
    first_run_id = 0
    if len(runs) > 0:
        first_run_id = runs[0].id

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (
        reverse("report:instrument_summary", args=[instrument]),
        instrument,
    )
    breadcrumbs += " &rsaquo; %s" % str(ipts_id).lower()

    template_values = {
        "instrument": instrument.upper(),
        "ipts_number": ipts,
        "run_list": run_list,
        "breadcrumbs": breadcrumbs,
        "ipts_url": ipts_url,
        "update_url": update_url,
        "first_run_id": first_run_id,
    }
    template_values = view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "report/ipts_summary.html", template_values)


@users_view_util.login_or_local_required
@cache_page(settings.SLOW_PAGE_CACHE_TIMEOUT)
@cache_control(private=True)
@vary_on_cookie
def live_errors(request, instrument):
    """
    Display the list of latest errors
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # TODO: let the user pick the timeframe for the errors.
    # Pick 30 days for now.
    time_period = 30
    delta_time = datetime.timedelta(days=time_period)
    oldest_time = timezone.now() - delta_time
    error_query = Error.objects.filter(
        run_status_id__created_on__gte=oldest_time,
        run_status_id__run_id__instrument_id=instrument_id,
    ).order_by("id")
    last_error_id = 0
    if len(error_query) > 0:
        last_error_id = error_query[len(error_query) - 1].id
    error_list = []
    for err in error_query:
        localtime = timezone.localtime(err.run_status_id.created_on)
        error_list.append(
            {
                "experiment": str(
                    "<a href='%s'>%s</a>"
                    % (
                        reverse(
                            "report:ipts_summary",
                            args=[
                                instrument,
                                err.run_status_id.run_id.ipts_id.expt_name,
                            ],
                        ),
                        err.run_status_id.run_id.ipts_id.expt_name,
                    )
                ),
                "run": str(
                    "<a href='%s'>%s</a>"
                    % (
                        reverse(
                            "report:detail",
                            args=[instrument, err.run_status_id.run_id.run_number],
                        ),
                        err.run_status_id.run_id.run_number,
                    )
                ),
                "info": str(err.description),
                "timestamp": err.run_status_id.created_on.isoformat(),
                "created_on": formats.localize(localtime),
            }
        )

    # Instrument reporting URL
    instrument_url = reverse("report:instrument_summary", args=[instrument])
    update_url = reverse("report:get_error_update", args=[instrument])

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (
        reverse("report:instrument_summary", args=[instrument]),
        instrument,
    )
    breadcrumbs += " &rsaquo; errors"

    template_values = {
        "instrument": instrument.upper(),
        "error_list": error_list,
        "last_error_id": last_error_id,
        "breadcrumbs": breadcrumbs,
        "instrument_url": instrument_url,
        "update_url": update_url,
        "time_period": time_period,
    }
    template_values = view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render(request, "report/live_errors.html", template_values)


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_experiment_update(request, instrument, ipts):
    """
    Ajax call to get updates behind the scenes

    :param instrument: instrument name
    :param ipts: experiment name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    # Get experiment
    ipts_id = get_object_or_404(IPTS, expt_name=ipts, instruments=instrument_id)

    # Get last experiment and last run
    data_dict = view_util.get_current_status(instrument_id)
    data_dict = dasmon_view_util.get_live_runs_update(request, instrument_id, ipts_id, **data_dict)

    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response["Connection"] = "close"
    return response


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_instrument_update(request, instrument):
    """
    Ajax call to get updates behind the scenes

    :param instrument: instrument name
    """
    since = request.GET.get("since", "0")
    try:
        since = int(since)
        since_expt_id = get_object_or_404(IPTS, id=since)
    except:  # noqa: E722
        since = 0
        since_expt_id = None

    # Get the instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Get last experiment and last run
    data_dict = view_util.get_current_status(instrument_id)
    expt_list = IPTS.objects.filter(instruments=instrument_id, id__gt=since).order_by("created_on")

    update_list = []
    if since_expt_id is not None and len(expt_list) > 0:
        data_dict["last_expt_id"] = expt_list[0].id
        for e in expt_list:
            if since_expt_id.created_on < e.created_on:
                localtime = timezone.localtime(e.created_on)
                expt_dict = {
                    "ipts": e.expt_name.upper(),
                    "n_runs": e.number_of_runs(),
                    "created_on": formats.localize(localtime),
                    "timestamp": e.created_on.isoformat(),
                    "ipts_id": e.id,
                }
                update_list.append(expt_dict)
    data_dict["expt_list"] = update_list
    data_dict["refresh_needed"] = "1" if len(update_list) > 0 else "0"

    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response["Connection"] = "close"
    return response


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_error_update(request, instrument):
    """
    Ajax call to get updates behind the scenes

    :param instrument: instrument name
    :param ipts: experiment name
    """
    since = request.GET.get("since", "0")
    try:
        since = int(since)
        last_error_id = get_object_or_404(Error, id=since)
    except:  # noqa: E722
        last_error_id = None

    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    # Get last experiment and last run
    data_dict = view_util.get_current_status(instrument_id)

    err_list = []
    if last_error_id is not None:
        errors = Error.objects.filter(
            run_status_id__run_id__instrument_id=instrument_id, id__gt=last_error_id.id
        ).order_by("run_status_id__created_on")
        if len(errors) > 0:
            last_error_id_number = None
            for e in errors:
                if last_error_id_number is None:
                    last_error_id_number = e.id

                if last_error_id.run_status_id.created_on < e.run_status_id.created_on:
                    localtime = timezone.localtime(e.run_status_id.created_on)
                    err_dict = {
                        "run": e.run_status_id.run_id.run_number,
                        "ipts": e.run_status_id.run_id.ipts_id.expt_name,
                        "description": e.description,
                        "created_on": formats.localize(localtime),
                        "timestamp": e.run_status_id.created_on.isoformat(),
                        "error_id": e.id,
                    }
                    err_list.append(err_dict)
            data_dict["last_error_id"] = last_error_id_number
    data_dict["errors"] = err_list
    data_dict["refresh_needed"] = "1" if len(err_list) > 0 else "0"

    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response["Connection"] = "close"
    return response
