from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import simplejson, dateformat, timezone
from django.views.decorators.cache import cache_page
from django.conf import settings
import logging
import sys
import os

from report.models import DataRun, IPTS, Instrument, Error, RunStatus
from icat_server_communication import get_run_info
import datetime
import view_util
import users.view_util
import dasmon.view_util

@users.view_util.login_or_local_required
def summary(request):
    """
        List of available instruments
    """
    instruments = Instrument.objects.all().order_by('name')
    # Get base URL
    base_url = reverse('report.views.instrument_summary',args=['aaaa'])
    base_url = base_url.replace('/aaaa','')
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; summary" % reverse(settings.LANDING_VIEW)

    # Number of runs as a function of time
    max_date = datetime.datetime.now().replace(day=1).replace(tzinfo=timezone.get_current_timezone())
    epoch = datetime.datetime(1970,1,1).replace(tzinfo=timezone.get_current_timezone())
    adara_start = datetime.datetime(2012,10,1).replace(tzinfo=timezone.get_current_timezone())
    today = datetime.datetime.today().replace(tzinfo=timezone.get_current_timezone())
    # Fill in the partial data for the current month
    runs = DataRun.objects.filter(created_on__gte=max_date)
    run_rate = []
    run_summary = [{'min_date': max_date,
                    'max_date': datetime.datetime.today(),
                    'number_of_runs': len(runs)}]
    run_rate.append([1000*int((today-epoch).total_seconds()), len(runs)])
    while True:
        # Make sure we don't display zeros for the period before
        # the system was installed
        if max_date<adara_start:
            break
        # Start date
        month = max_date.month-1
        if month<=0:
            min_date = max_date.replace(month=12, year=max_date.year-1)
        else:
            min_date = max_date.replace(month=month)

        runs = DataRun.objects.filter(created_on__lt=max_date,
                                      created_on__gte=min_date)
        run_summary.append({'min_date': min_date,
                            'max_date': max_date,
                            'number_of_runs': len(runs)})
        run_rate.append([1000*int((max_date-epoch).total_seconds()), len(runs)])

        # Update end date
        month = max_date.month-1
        if month<=0:
            max_date = max_date.replace(month=12, year=max_date.year-1)
        else:
            max_date = max_date.replace(month=month)

    template_values = {'instruments':instruments,
                       'run_summary': run_summary,
                       'run_rate': run_rate,
                       'breadcrumbs':breadcrumbs,
                       'base_instrument_url':base_url}
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/global_summary.html',
                              template_values)

@users.view_util.login_or_local_required
@users.view_util.monitor
def detail(request, instrument, run_id):
    """
        Run details
        @param instrument: instrument name
        @param run_id: run number, as string
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    run_object = get_object_or_404(DataRun, instrument_id=instrument_id,run_number=run_id)

    icat_info = get_run_info(instrument, str(run_object.ipts_id), run_id)
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; run %s" % (reverse(settings.LANDING_VIEW),
            reverse('report.views.instrument_summary',args=[instrument]), instrument,
            reverse('report.views.ipts_summary',args=[instrument, run_object.ipts_id.expt_name]), str(run_object.ipts_id).lower(),  
            run_id          
            ) 
    
    # Check whether we need a re-reduce link
    reduce_url = None
    if view_util.needs_reduction(request, run_object):
        reduce_url = 'reduce'
    
    # Find status entries
    status_objects = RunStatus.objects.filter(run_id=run_id).order_by('created_on').reverse()

    # Look for an image of the reduction
    image_url = None
    try:
        from file_handling.models import ReducedImage
        images = ReducedImage.objects.filter(run_id=run_object)
        if len(images)>0:
            image = images.latest('created_on')
            if image is not None and bool(image.file) and os.path.isfile(image.file.path):
                image_url = image.file.url
    except:
        logging.error("Error finding reduced image: %s" % sys.exc_value)
    
    # Check whether this is the last known run for this instrument
    last_run_id = DataRun.objects.get_last_cached_run(instrument_id)
    if last_run_id == run_object:
        next_url = None
    else:
        try:
            DataRun.objects.get(instrument_id=instrument_id,
                                run_number=run_object.run_number+1)
            next_url = reverse('report.views.detail', args=[instrument, run_object.run_number+1])
        except:
            next_url = None

    # Get previous run
    try:
        DataRun.objects.get(instrument_id=instrument_id,
                            run_number=run_object.run_number-1)
        prev_url = reverse('report.views.detail', args=[instrument, run_object.run_number-1])
    except:
        prev_url = None
    
    template_values = {'instrument':instrument.upper(),
                       'run_object':run_object,
                       'status':status_objects,
                       'breadcrumbs':breadcrumbs,
                       'icat_info':icat_info,
                       'reduce_url':reduce_url,
                       'image_url':image_url,
                       'prev_url': prev_url,
                       'next_url': next_url,
                       }

    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = dasmon.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/detail.html', template_values)

@users.view_util.login_or_local_required
@users.view_util.monitor
def submit_for_reduction(request, instrument, run_id):
    """
        Send a run for automated reduction
        @param instrument: instrument name
        @param run_id: run number
    """
    return view_util.processing_request(request, instrument, run_id,
                                        destination='/queue/REDUCTION.REQUEST')    

@users.view_util.login_or_local_required
@users.view_util.monitor
def submit_for_post_processing(request, instrument, run_id):
    """
        Send a run for complete post-processing
        @param instrument: instrument name
        @param run_id: run number
    """
    return view_util.processing_request(request, instrument, run_id,
                                        destination='/queue/POSTPROCESS.DATA_READY')    
    
@users.view_util.login_or_local_required
@users.view_util.monitor
def submit_for_cataloging(request, instrument, run_id):
    """
        Send a run for cataloging
        @param instrument: instrument name
        @param run_id: run number
    """
    return view_util.processing_request(request, instrument, run_id,
                                        destination='/queue/CATALOG.REQUEST')

@users.view_util.login_or_local_required
@users.view_util.monitor
def instrument_summary(request, instrument):
    """
        Instrument summary page
        @param instrument: instrument name
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # Get list of IPTS
    ipts, ipts_header = view_util.ExperimentSorter(request)(instrument_id)    
    
    # Instrument error URL
    error_url = reverse('report.views.live_errors',args=[instrument])

    # Update URL for live monitoring
    update_url = reverse('report.views.get_instrument_update',args=[instrument])
    
    # Get the last IPTS created so that we can properly do the live update
    if IPTS.objects.filter(instruments=instrument_id).count()>0:
        last_expt_created = IPTS.objects.filter(instruments=instrument_id).latest('id')
    else:
        last_expt_created = None
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s" % (reverse(settings.LANDING_VIEW),
                                                         instrument.lower()
                                                         ) 

    template_values = {'instrument':instrument.upper(),
                       'ipts':ipts,
                       'ipts_header':ipts_header,
                       'breadcrumbs':breadcrumbs,
                       'error_url': error_url,
                       'update_url':update_url,
                       'last_expt_created':last_expt_created,
                       }
    template_values = view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/instrument.html', template_values)

@users.view_util.login_or_local_required
@users.view_util.monitor
def ipts_summary(request, instrument, ipts):
    """
        Experiment summary giving the list of runs
        @param instrument: instrument name
        @param ipts: experiment name
    """
    # Protect against lower-case requests
    ipts = ipts.upper()
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    # Get experiment
    ipts_id = get_object_or_404(IPTS, expt_name=ipts, instruments=instrument_id)
    
    # Get IPTS URL
    ipts_url = reverse('report.views.ipts_summary',args=[instrument,ipts])
    update_url = reverse('report.views.get_experiment_update',args=[instrument,ipts])

    # Get the latest run and experiment so we can determine later
    # whether the user should refresh the page
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    runs = DataRun.objects.filter(instrument_id=instrument_id,
                                  ipts_id=ipts_id).order_by('created_on')
    run_list = view_util.get_run_list_dict(runs)

    # Get the ID of the first displayed run so that we can update the
    # status of runs that are displayed
    first_run_id = 0
    if len(runs)>0:
        first_run_id = runs[0].id

    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse(settings.LANDING_VIEW),
            reverse('report.views.instrument_summary',args=[instrument]), instrument,
            str(ipts_id).lower()
            ) 

    template_values = {'instrument': instrument.upper(),
                       'ipts_number': ipts,
                       'run_list': run_list,
                       'breadcrumbs': breadcrumbs,
                       'ipts_url': ipts_url,
                       'update_url': update_url,
                       'first_run_id': first_run_id,
                       }
    template_values = view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/ipts_summary.html', template_values)
    
@users.view_util.login_or_local_required
@users.view_util.monitor
def live_errors(request, instrument):
    """
        Display the list of latest errors
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
        
    query_filter = request.GET.get('show', 'recent').lower()
    show_all = query_filter=='all'
    try:
        n_max = int(query_filter)
    except:
        n_max = 20

    # Get list of errors
    errors, errors_header = view_util.ErrorSorter(request)(instrument_id)
    number_of_errors = len(errors)
    if not show_all and len(errors)>n_max:
        errors = errors[:n_max]
    
    # Instrument reporting URL
    instrument_url = reverse('report.views.instrument_summary',args=[instrument])
    error_url = reverse('report.views.live_errors',args=[instrument])
    
    update_url = reverse('report.views.get_error_update',args=[instrument])
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse(settings.LANDING_VIEW),
            reverse('report.views.instrument_summary',args=[instrument]), instrument, "errors"
            )

    template_values = {'instrument':instrument.upper(),
                       'error_list':errors,
                       'error_header':errors_header,
                       'breadcrumbs':breadcrumbs,
                       'all_shown':show_all,
                       'number_shown':len(errors),
                       'number_of_errors':number_of_errors,
                       'instrument_url':instrument_url,
                       'error_url':error_url,
                       'update_url':update_url,
                       }
    template_values = view_util.fill_template_values(request, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('report/live_errors.html', template_values)
    
@users.view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_experiment_update(request, instrument, ipts):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
         @param ipts: experiment name
    """ 
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    # Get experiment
    ipts_id = get_object_or_404(IPTS, expt_name=ipts, instruments=instrument_id)
    
    # Get last experiment and last run
    data_dict = view_util.get_current_status(instrument_id)    
    data_dict = dasmon.view_util.get_live_runs_update(request, instrument_id, ipts_id, **data_dict)
    
    response = HttpResponse(simplejson.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response


@users.view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_instrument_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
    """ 
    since = request.GET.get('since', '0')
    try:
        since = int(since)
        since_expt_id = get_object_or_404(IPTS, id=since)
    except:
        since = 0
        since_expt_id = None
    
    # Get the instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    
    # Get last experiment and last run
    data_dict = view_util.get_current_status(instrument_id)
    expt_list = IPTS.objects.filter(instruments=instrument_id, id__gt=since).order_by('created_on')

    update_list = []
    if since_expt_id is not None and len(expt_list)>0:
        data_dict['last_expt_id'] = expt_list[0].id
        for e in expt_list:
            if since_expt_id.created_on < e.created_on:
                localtime = timezone.localtime(e.created_on)
                df = dateformat.DateFormat(localtime)
                expt_dict = {"ipts":e.expt_name.upper(),
                            "n_runs":e.number_of_runs(),
                            "timestamp":df.format(settings.DATETIME_FORMAT),
                            "ipts_id":e.id,
                            }
                update_list.append(expt_dict)
    data_dict['expt_list'] = update_list
    data_dict['refresh_needed'] = '1' if len(update_list)>0 else '0'
    
    response = HttpResponse(simplejson.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response

  
@users.view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def get_error_update(request, instrument):
    """
         Ajax call to get updates behind the scenes
         @param instrument: instrument name
         @param ipts: experiment name
    """ 
    since = request.GET.get('since', '0')
    try:
        since = int(since)
        last_error_id = get_object_or_404(Error, id=since)
    except:
        last_error_id = None
    
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())    
    
    # Get last experiment and last run
    data_dict = view_util.get_current_status(instrument_id)    
    
    err_list = []
    if last_error_id is not None:
        errors = Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id,
                                      id__gt=last_error_id.id).order_by('run_status_id__created_on')        
        if len(errors)>0:
            last_error_id_number = None
            for e in errors:
                if last_error_id_number is None:
                    last_error_id_number = e.id
                    
                if last_error_id.run_status_id.created_on<e.run_status_id.created_on:
                    localtime = timezone.localtime(e.run_status_id.created_on)
                    df = dateformat.DateFormat(localtime)
                    err_dict = {"run":e.run_status_id.run_id.run_number,
                                "ipts":e.run_status_id.run_id.ipts_id.expt_name,
                                "description":e.description,
                                "timestamp":df.format(settings.DATETIME_FORMAT),
                                "error_id":e.id,
                                }
                    err_list.append(err_dict)
            data_dict['last_error_id'] = last_error_id_number
    data_dict['errors'] = err_list
    data_dict['refresh_needed'] = '1' if len(err_list)>0 else '0'
    
    response = HttpResponse(simplejson.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response


