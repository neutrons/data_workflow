# pylint: disable=invalid-name, line-too-long, too-many-locals, bare-except, unused-argument
"""
Report views

@author: M. Doucet, Oak Ridge National Laboratory
@copyright: 2014-2015 Oak Ridge National Laboratory
"""
import sys
import logging
import datetime
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_cookie
from django.conf import settings
from django.contrib.auth.decorators import login_required


from reporting.dasmon.models import ActiveInstrument
from reporting.report.models import DataRun, IPTS, Instrument, RunStatus
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

    # Instrument error URL
    error_url = reverse("report:live_errors", args=[instrument])

    # Update URL for live monitoring
    update_url = reverse("report:get_instrument_update", args=[instrument])

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s" % (
        reverse(settings.LANDING_VIEW),
        instrument.lower(),
    )

    template_values = {
        "instrument": instrument.upper(),
        "breadcrumbs": breadcrumbs,
        "error_url": error_url,
        "update_url": update_url,
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

    # Get data URL
    update_url = reverse("report:get_experiment_update", args=[instrument, ipts])

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
        "breadcrumbs": breadcrumbs,
        "update_url": update_url,
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
        "breadcrumbs": breadcrumbs,
        "instrument_url": instrument_url,
        "update_url": update_url,
        "time_period": 30,
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

    # map for sorting columns
    column_to_field = {
        "run": "run_number",
        "timestamp": "created_on",
    }

    order_column_number = request.GET.get("order[0][column]", "0")
    order_dir = request.GET.get("order[0][dir]", "desc")
    order_column = request.GET.get(f"columns[{order_column_number}][data]", "run")
    order_column = column_to_field.get(order_column, "run_number")

    limit = int(request.GET.get("length", 10))
    offset = int(request.GET.get("start", 0))
    draw = int(request.GET.get("draw", 1))

    run_search = request.GET.get("columns[0][search][value]", "")
    date_search = request.GET.get("columns[1][search][value]", "")
    status_search = request.GET.get("columns[2][search][value]", "")

    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    # Get experiment
    ipts_id = get_object_or_404(IPTS, expt_name=ipts, instruments=instrument_id)

    data = view_util.get_current_status(instrument_id)

    run_list, count, filtered_count = dasmon_view_util.get_run_list_ipts(
        instrument_id,
        ipts_id,
        offset,
        limit,
        order_column,
        order_dir == "desc",
        run_search,
        date_search,
        status_search,
    )
    data["data"] = view_util.get_run_list_dict(run_list)
    data["recordsTotal"] = count
    data["recordsFiltered"] = filtered_count
    data["draw"] = draw

    return JsonResponse(data)


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_instrument_update(request, instrument):
    """
    Ajax call to get updates behind the scenes

    :param instrument: instrument name
    """

    # map for sorting columns
    column_to_field = {
        "experiment": "expt_name",
        "created_on": "created_on",
        "total": "number_of_runs",
    }

    order_column_number = request.GET.get("order[0][column]", "2")
    order_dir = request.GET.get("order[0][dir]", "desc")
    order_column = request.GET.get(f"columns[{order_column_number}][data]", "run")
    order_column = column_to_field.get(order_column, "created_on")

    limit = int(request.GET.get("length", 10))
    offset = int(request.GET.get("start", 0))
    draw = int(request.GET.get("draw", 1))

    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    data_dict = view_util.get_current_status(instrument_id)

    expt_list, count = view_util.get_experiment_list(instrument_id, offset, limit, order_column, order_dir == "desc")

    data_dict["data"] = expt_list
    data_dict["recordsTotal"] = count
    data_dict["recordsFiltered"] = count
    data_dict["draw"] = draw

    return JsonResponse(data_dict)


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_error_update(request, instrument):
    """
    Ajax call to get updates behind the scenes

    :param instrument: instrument name
    :param ipts: experiment name
    """

    limit = int(request.GET.get("length", 10))
    offset = int(request.GET.get("start", 0))
    draw = int(request.GET.get("draw", 1))

    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    data_dict = view_util.get_current_status(instrument_id)

    error_list, count = view_util.get_error_list(instrument_id, offset, limit)

    data_dict["data"] = error_list
    data_dict["recordsTotal"] = count
    data_dict["recordsFiltered"] = count
    data_dict["draw"] = draw

    return JsonResponse(data_dict)
