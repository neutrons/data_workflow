"""
    Status monitor utilities to support 'report' views

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
import sys
import os
import logging
import json
import datetime
import string
import httplib2
import re
import hashlib
from report.models import (DataRun, RunStatus, IPTS, Instrument,
                           Error, StatusQueue, Task, WorkflowSummary)
from django.urls import reverse
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect
from django.utils import dateformat, timezone
from django.conf import settings
from django.db import connection, transaction
from django.core.cache import cache

import dasmon.view_util
import reporting_app.view_util


def generate_key(instrument: str, run_id: int):
    """
        Generate a secret key for a run on a given instrument
        @param instrument: instrument name
        @param run_id: run number
    """
    if not hasattr(settings, "LIVE_PLOT_SECRET_KEY"):
        return None
    secret_key = settings.LIVE_PLOT_SECRET_KEY
    if len(secret_key) == 0:
        return None
    else:
        h = hashlib.sha1()
        h.update(("%s%s%s" % (instrument.upper(), secret_key, run_id)).encode("utf-8"))
        return h.hexdigest()


def append_key(input_url, instrument, run_id):
    """
        Append a live data secret key to a url
        @param input_url: url to modify
        @param instrument: instrument name
        @param run_id: run number
    """
    client_key = generate_key(instrument, run_id)
    if client_key is None:
        return input_url
    # Determine whether this is the first query string argument of the url
    delimiter = '&' if '/?' in input_url else '?'
    return "%s%skey=%s" % (input_url, delimiter, client_key)


def fill_template_values(request, **template_args):
    """
        Fill the template argument items needed to populate
        side bars and other satellite items on the pages.

        Only the arguments common to all pages will be filled.
    """
    if "instrument" not in template_args:
        return template_args

    instr = template_args["instrument"].lower()
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instr)

    # Get last experiment and last run
    last_run_id = DataRun.objects.get_last_cached_run(instrument_id)
    if last_run_id is None:
        last_expt_id = IPTS.objects.get_last_ipts(instrument_id)
    else:
        last_expt_id = last_run_id.ipts_id
    template_args['last_expt'] = last_expt_id
    template_args['last_run'] = last_run_id

    # Get base IPTS URL
    base_ipts_url = reverse('report:ipts_summary', args=[instr, '0000'])
    base_ipts_url = base_ipts_url.replace('/0000', '')
    template_args['base_ipts_url'] = base_ipts_url

    # Get base Run URL
    base_run_url = reverse('report:detail', args=[instr, '0000'])
    base_run_url = base_run_url.replace('/0000', '')
    template_args['base_run_url'] = base_run_url

    # Get run rate and error rate
    r_rate, e_rate = retrieve_rates(instrument_id, last_run_id)
    template_args['run_rate'] = str(r_rate)
    template_args['error_rate'] = str(e_rate)

    template_args = dasmon.view_util.fill_template_values(request, **template_args)

    return template_args


def needs_reduction(request, run_id):
    """
        Determine whether we need a reduction link to
        submit a run for automated reduction
        @param request: HTTP request object
        @param run_id: DataRun object
    """
    # Get REDUCTION.DATA_READY queue
    try:
        red_queue = StatusQueue.objects.get(name="REDUCTION.DATA_READY")
    except StatusQueue.DoesNotExist:
        logging.error(sys.exc_info()[1])
        return False

    # Check whether we have a task for this queue
    tasks = Task.objects.filter(instrument_id=run_id.instrument_id,
                                input_queue_id=red_queue)
    if len(tasks) == 1 and \
        (tasks[0].task_class is None or len(tasks[0].task_class) == 0) \
            and len(tasks[0].task_queue_ids.all()) == 0:
        return False

    return True


def send_processing_request(instrument_id, run_id, user=None, destination=None, is_complete=False):
    """
        Send an AMQ message to the workflow manager to reprocess
        the run
        @param instrument_id: Instrument object
        @param run_id: DataRun object
    """
    if destination is None:
        destination = '/queue/POSTPROCESS.DATA_READY'

    # IPTS name
    try:
        ipts = run_id.ipts_id.expt_name.upper()
    except:
        ipts = str(run_id.ipts_id)

    # Verify that we have a file path.
    # If not, look up the online catalog
    file_path = run_id.file
    if len(file_path) == 0:
        from report.catalog import get_run_info

        run_info = get_run_info(str(instrument_id), '', run_id.run_number)
        for _file in run_info['data_files']:
            if _file.endswith('_event.nxs') or _file.endswith('.nxs.h5'):
                file_path = _file
        # If we don't have the IPTS, fill it in too
        if len(ipts) == 0:
            ipts = run_info['proposal']

    # Get facility from file path
    toks = file_path.split('/')
    facility_name = 'SNS'
    if hasattr(settings, 'FACILITY_INFO'):
        facility_name = settings.FACILITY_INFO.get(str(instrument_id), 'SNS')
    if len(toks) > 1:
        facility_name = toks[1].upper()
    # Sanity check
    if len(file_path) == 0 or len(ipts) == 0 or ipts is None:
        logging.error("No catalog information for run %s: message not sent", run_id)
        raise RuntimeError("Run %s not found in catalog" % str(run_id))
    # Build up dictionary
    data_dict = {'facility': facility_name,
                 'instrument': str(instrument_id),
                 'ipts': ipts,
                 'run_number': run_id.run_number,
                 'data_file': file_path
                 }
    if is_complete is True:
        data_dict['is_complete'] = 'true'
    if user is not None:
        data_dict['information'] = "Requested by %s" % user

    data = json.dumps(data_dict)
    reporting_app.view_util.send_activemq_message(destination, data)
    logging.info("Reduction requested: %s", str(data))


def processing_request(request, instrument, run_id, destination):
    """
        Process a request for post-processing
        @param instrument: instrument name
        @param run_id: run number [string]
        @param destination: outgoing AMQ queue
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    run_object = get_object_or_404(DataRun, instrument_id=instrument_id, run_number=run_id)
    try:
        send_processing_request(instrument_id, run_object, request.user,
                                destination=destination)
    except:
        logging.error("Could not send post-processing request: %s", destination)
        logging.error(sys.exc_info()[1])
        return HttpResponseServerError()
    # return render(request, 'report/processing_request_failure.html', {})
    return redirect(reverse('report:detail', args=[instrument, run_id]))


def retrieve_rates(instrument_id, last_run_id):
    """
        Retrieve the run rate and error rate for an instrument.
        Try to get it from the cache if possible.
        @param instrument_id: Instrument object
        @param last_run_id: DataRun object
    """
    last_run = None
    if last_run_id is not None:
        last_run = last_run_id.run_number

    # Check whether we have a cached value and whether it is up to date
    last_cached_run = cache.get('%s_rate_last_run' % instrument_id.name)

    def _get_rate(id_name):
        """
            Returns rate for runs or errors
            @param id_name: 'run' or 'error'
        """
        rate = cache.get('%s_%s_rate' % (instrument_id.name, id_name))
        if rate is not None and last_cached_run is not None and last_run == last_cached_run:
            return cache.get('%s_%s_rate' % (instrument_id.name, id_name))
        return None

    runs = _get_rate('run')
    errors = _get_rate('error')

    # If we didn't find good rates in the cache, recalculate them
    if runs is None or errors is None:
        runs = run_rate(instrument_id)
        errors = error_rate(instrument_id)
        cache.set('%s_run_rate' % instrument_id.name, runs, settings.RUN_RATE_CACHE_TIMEOUT)
        cache.set('%s_error_rate' % instrument_id.name, errors, settings.RUN_RATE_CACHE_TIMEOUT)
        cache.set('%s_rate_last_run' % instrument_id.name, last_run)

    return runs, errors


@transaction.atomic
def run_rate(instrument_id, n_hours=24):
    """
        Returns the rate of new runs for the last n_hours hours.
        @param instrument_id: Instrument model object
        @param n_hours: number of hours to track
    """
    # Try calling the stored procedure (faster)
    try:
        cursor = connection.cursor()
        cursor.callproc("run_rate", (instrument_id.id,))
        msg = cursor.fetchone()[0]
        cursor.execute('FETCH ALL IN "%s"' % msg)
        rows = cursor.fetchall()
        cursor.close()
        return [[int(r[0]), int(r[1])] for r in rows]
    except:
        connection.close()
        logging.error("Run rate (%s): %s", str(instrument_id), sys.exc_info()[1])

        # Do it by hand (slow)
        time = timezone.now()
        runs = []
        running_sum = 0
        for i in range(n_hours):
            t_i = time - datetime.timedelta(hours=i + 1)
            n = DataRun.objects.filter(instrument_id=instrument_id, created_on__gte=t_i).count()
            n -= running_sum
            running_sum += n
            runs.append([-i, n])
        return runs


@transaction.atomic
def error_rate(instrument_id, n_hours=24):
    """
        Returns the rate of errors for the last n_hours hours.
        @param instrument_id: Instrument model object
        @param n_hours: number of hours to track
    """
    # Try calling the stored procedure (faster)
    try:
        cursor = connection.cursor()
        cursor.callproc("error_rate", (instrument_id.id,))
        msg = cursor.fetchone()[0]
        cursor.execute('FETCH ALL IN "%s"' % msg)
        rows = cursor.fetchall()
        cursor.close()
        return [[int(r[0]), int(r[1])] for r in rows]
    except:
        connection.close()
        logging.error("Error rate (%s): %s", str(instrument_id), sys.exc_info()[1])

        # Do it by hand (slow)
        time = timezone.now()
        errors = []
        running_sum = 0
        for i in range(n_hours):
            t_i = time - datetime.timedelta(hours=i + 1)
            n = Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id,
                                     run_status_id__created_on__gte=t_i).count()
            n -= running_sum
            running_sum += n
            errors.append([-i, n])
        return errors


def get_current_status(instrument_id):
    """
        Get current status information such as the last
        experiment/run for a given instrument.

        Used to populate AJAX response, so must not contain Model objects

        @param instrument_id: Instrument model object
    """
    # Get last experiment and last run
    last_run_id = DataRun.objects.get_last_cached_run(instrument_id)
    if last_run_id is None:
        last_expt_id = IPTS.objects.get_last_ipts(instrument_id)
    else:
        last_expt_id = last_run_id.ipts_id

    r_rate, e_rate = retrieve_rates(instrument_id, last_run_id)
    data_dict = {'run_rate': r_rate, 'error_rate': e_rate}

    if last_run_id is not None:
        localtime = timezone.localtime(last_run_id.created_on)
        df = dateformat.DateFormat(localtime)
        data_dict['last_run_id'] = last_run_id.id
        data_dict['last_run'] = last_run_id.run_number
        data_dict['last_run_time'] = df.format(settings.DATETIME_FORMAT)

    if last_expt_id is not None:
        data_dict['last_expt_id'] = last_expt_id.id
        data_dict['last_expt'] = last_expt_id.expt_name.upper()

    return data_dict


def is_acquisition_complete(run_id):
    """
        Determine whether the acquisition is complete and post-processing
        has started
        @param run_id: run object
    """
    status_items = RunStatus.objects.filter(run_id=run_id,
                                            queue_id__name='POSTPROCESS.DATA_READY')
    return len(status_items) > 0


def get_post_processing_status(red_timeout=0.25, yellow_timeout=120):
    """
        Get the health status of post-processing services
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    # The cataloging and reduction status is more confusing than anything,
    # so we are phasing it out.
    return {"catalog": 0, "reduction": 0}


def get_run_status_text(run_id, show_error=False, use_element_id=False):
    """
        Get a textual description of the current status
        for a given run
        @param run_id: run object
        @param show_error: if true, the last error will be whow, otherwise "error"
    """
    status = 'unknown'
    try:
        if use_element_id:
            element_id = "id='run_id_%s'" % run_id.id
        else:
            element_id = ''
        s = WorkflowSummary.objects.get(run_id=run_id)
        if s.complete is True:
            status = "<span %s class='green'>complete</span>" % element_id
        else:
            last_error = run_id.last_error()
            if last_error is not None:
                if show_error:
                    status = "<span %s class='red'>%s</span>" % (element_id, last_error)
                else:
                    status = "<span %s class='red'><b>error</b></span>" % element_id
            else:
                status = "<span %s class='red'>incomplete</span>" % element_id
    except:
        logging.error("report.view_util.get_run_status_text: %s", sys.exc_info()[1])
    return status


def get_run_list_dict(run_list):
    """
        Get a list of run object and transform it into a list of
        dictionaries that can be used to fill a table.

        @param run_list: list of run object (usually a QuerySet)
    """
    run_dicts = []
    try:
        for r in run_list:
            localtime = timezone.localtime(r.created_on)
            df = dateformat.DateFormat(localtime)

            run_url = reverse('report:detail', args=[str(r.instrument_id), r.run_number])
            reduce_url = reverse('report:submit_for_reduction', args=[str(r.instrument_id), r.run_number])
            instr_url = reverse('dasmon:live_runs', args=[str(r.instrument_id)])

            run_dicts.append({"instrument_id": str("<a href='%s'>%s</a>" % (instr_url, str(r.instrument_id))),
                              "run": str("<a href='%s'>%s</a>" % (run_url, r.run_number)),
                              "reduce_url": str("<a id='reduce_%s' href='javascript:void(0);' onClick='$.ajax({ url: \"%s\", cache: false }); $(\"#reduce_%s\").remove();'>reduce</a>"  # noqa: E501
                                                % (r.run_number, reduce_url, r.run_number)),
                              "run_id": r.id,
                              "timestamp": str(df.format(settings.DATETIME_FORMAT)),
                              "status": get_run_status_text(r, use_element_id=True)
                              })
    except:
        logging.error("report.view_util.get_run_list_dict: %s", sys.exc_info()[1])
    return run_dicts


def extract_ascii_from_div(html_data, trace_id=None):
    """
        Extract data from an plot <div>.
        Only returns the first one it finds.
        @param html_data: <div> string

        #TODO: allow to specify which trace to return in cases where we have multiple curves
    """
    try:
        result = re.search(r"newPlot\((.*)\)</script>", html_data)
        jsondata_str = "[%s]" % result.group(1)
        data_list = json.loads(jsondata_str)
        ascii_data = ""
        for d in data_list:
            if isinstance(d, list):
                # Only allow a single trace
                if trace_id is None and len(d) > 1:
                    logging.debug("Multiple traces found, and no ID was specified")
                    return None
                for trace in d:
                    if 'type' in trace and trace['type'] == 'scatter':
                        x = trace['x']
                        y = trace['y']
                        dx = [0] * len(x)
                        dy = [0] * len(y)
                        if 'error_x' in trace and 'array' in trace['error_x']:
                            dx = trace['error_x']['array']
                        if 'error_y' in trace and 'array' in trace['error_y']:
                            dy = trace['error_y']['array']
                        break
                for i in range(len(x)):
                    ascii_data += "%g %g %g %g\n" % (x[i], y[i], dy[i], dx[i])
                return ascii_data
    except:
        # Unable to extract data from <div>
        logging.debug("Unable to extract data from <div>: %s", sys.exc_info()[1])
    return None


def get_plot_template_dict(run_object=None, instrument=None, run_id=None):
    """
        Get template dictionary for plots
        @param run_object: DataRun object
        @param instrument: instrument name
        @param run_id: run_number
    """
    plot_dict = {'image_url': None,
                 'plot_data': None,
                 'html_data': None,
                 'plot_label_x': '',
                 'plot_label_y': '',
                 'update_url': None}

    url_template = string.Template(settings.LIVE_DATA_SERVER)
    live_data_url = url_template.substitute(instrument=instrument, run_number=run_id)
    live_data_url = "https://%s:%s%s" % (settings.LIVE_DATA_SERVER_DOMAIN,
                                         settings.LIVE_DATA_SERVER_PORT, live_data_url)

    # First option: html data
    html_data = get_plot_data_from_server(instrument, run_id, 'html')
    if html_data is not None:
        plot_dict['html_data'] = html_data
        plot_dict['update_url'] = append_key("%s/html/" % live_data_url, instrument, run_id)
        if extract_ascii_from_div(html_data) is not None:
            plot_dict['data_url'] = reverse('report:download_reduced_data', args=[instrument, run_id])
        return plot_dict

    # Second, json data from the plot server
    json_data = get_plot_data_from_server(instrument, run_id, 'json')

    # Third, local json data for the d3 plots
    if json_data is None:
        json_data = get_local_plot_data(run_object)
    else:
        plot_dict['update_url'] = append_key("%s/json/" % live_data_url, instrument, run_id)

    plot_data, x_label, y_label = extract_d3_data_from_json(json_data)
    if plot_data is not None:
        plot_dict['plot_data'] = plot_data
        plot_dict['plot_label_x'] = x_label
        plot_dict['plot_label_y'] = y_label
        return plot_dict

    # Fourth, get a local image
    plot_dict['image_url'] = get_local_image_url(run_object)
    return plot_dict


def get_local_image_url(run_object):
    """
        Get url for plot data served by this application
        @param run_object: DataRun object
    """
    image_url = None
    try:
        from file_handling.models import ReducedImage
        images = ReducedImage.objects.filter(run_id=run_object)
        if len(images) > 0:
            image = images.latest('created_on')
            if image is not None and bool(image.file) and os.path.isfile(image.file.path):
                image_url = image.file.url
    except:
        logging.error("Error finding reduced image: %s", sys.exc_info()[1])
    return image_url


def get_plot_data_from_server(instrument, run_id, data_type='json'):
    """
        Get json data from the live data server
        @param instrument: instrument name
        @param run_id: run number
        @param data_type: data type, either 'json' or 'html'
    """
    json_data = None
    try:
        url_template = string.Template(settings.LIVE_DATA_SERVER)
        live_data_url = url_template.substitute(instrument=instrument, run_number=run_id)
        live_data_url += "/%s/" % data_type
        live_data_url = append_key(live_data_url, instrument, run_id)
        conn = httplib2.HTTPSConnectionWithTimeout(settings.LIVE_DATA_SERVER_DOMAIN, timeout=1.5)
        conn.request('GET', live_data_url)
        data_request = conn.getresponse()
        if data_request.status == 200:
            json_data = data_request.read()
    except:
        logging.error("Could not pull data from live data server:\n%s", sys.exc_info()[1])
    return json_data


def get_local_plot_data(run_object):
    """
        Get json data served by this application
        @param run_object: DataRun object
    """
    from file_handling.models import JsonData
    json_data = None

    try:
        json_data_list = JsonData.objects.filter(run_id=run_object)
        if len(json_data_list) > 0:
            json_data_entry = json_data_list.latest('created_on')
            if json_data_entry is not None:
                json_data = json_data_entry.data
    except:
        logging.error("Could not pull data from live data server:\n%s", sys.exc_info()[1])
    return json_data


def extract_d3_data_from_json(json_data):
    """
        DEPRECATED

        For backward compatibility, extract D3 data from json data for
        the old-style interactive plots.
        @param json_data: json data block
    """
    plot_data = None
    x_label = "Q [1/\u00C5]"
    y_label = "Absolute reflectivity"

    # Return dummy data if not data is coming in.
    if json_data is None:
        return plot_data, x_label, y_label

    try:
        data_dict = json.loads(json_data)
        if 'main_output' in data_dict:
            # Old format
            if 'x' in data_dict['main_output']:
                x_values = data_dict['main_output']['x']
                y_values = data_dict['main_output']['y']
                e_values = data_dict['main_output']['e']
                if 'x_label' in data_dict['main_output']:
                    x_label = data_dict['main_output']['x_label']
                if 'y_label' in data_dict['main_output']:
                    y_label = data_dict['main_output']['y_label']
                plot_data = [[x_values[i], y_values[i], e_values[i]] for i in range(len(y_values))]
            # New format from Mantid
            elif 'data' in data_dict['main_output']:
                x_values = data_dict['main_output']['data']['1'][0]
                y_values = data_dict['main_output']['data']['1'][1]
                e_values = data_dict['main_output']['data']['1'][2]
                if 'axes' in data_dict['main_output']:
                    if 'xlabel' in data_dict['main_output']['axes']:
                        x_label = data_dict['main_output']['axes']['xlabel']
                    if 'ylabel' in data_dict['main_output']['axes']:
                        y_label = data_dict['main_output']['axes']['ylabel']
                if len(data_dict['main_output']['data']['1']) > 3:
                    dx = data_dict['main_output']['data']['1'][3]
                    plot_data = [[x_values[i], y_values[i], e_values[i], dx[i]] for i in range(len(y_values))]
                else:
                    plot_data = [[x_values[i], y_values[i], e_values[i]] for i in range(len(y_values))]
    except:
        logging.error("Error finding reduced json data: %s", sys.exc_info()[1])
    return plot_data, x_label, y_label


def find_skipped_runs(instrument_id, start_run_number=0):
    """
        Find run numbers that were skipped for a given instrument
        @param instrument_id: Instrument object
        @param start_run_number: run number to start from
    """
    missing_runs = []
    try:
        last_run_id = DataRun.objects.get_last_run(instrument_id)
        last_run_number = last_run_id.run_number
        # Use a reasonable default for the start run number
        if start_run_number == 0:
            start_run_number = max(0, last_run_number - 1000)
        for i in range(start_run_number, last_run_number):
            query_set = DataRun.objects.filter(instrument_id=instrument_id, run_number=i)
            if len(query_set) == 0:
                missing_runs.append(i)
    except:
        logging.error("Error finding missing runs: %s", sys.exc_info()[1])
    return missing_runs
