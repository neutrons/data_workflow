"""
    Automated reduction configuration view

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.conf import settings
from django.utils import dateparse, timezone
from models import ReductionProperty
from report.models import Instrument
import logging
import json
import sys
import datetime
from . import forms
from django.forms.formsets import formset_factory

import users.view_util
import dasmon.view_util
import view_util

@users.view_util.login_or_local_required
def configuration(request, instrument):
    """
        View current automated reduction configuration and modification history
        for a given instrument

        #TODO: redirect to another page if you are not part of the instrument team

        @param request: request object
        @param instrument: instrument name
    """
    if instrument.lower() in ['seq', 'arcs']:
        return configuration_dgs(request, instrument)
    if instrument.lower() == 'corelli':
        return configuration_corelli(request, instrument)
    if instrument.lower() == 'cncs':
        return configuration_cncs(request, instrument)

    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    props_list = ReductionProperty.objects.filter(instrument=instrument_id)
    params_list = []
    for item in props_list:
        params_list.append({"key": str(item.key),
                            "raw_value": str(item.value),
                            "value": "<form action='javascript:void(0);' onsubmit='update(this);'><input type='hidden' name='key' value='%s'><input title='Hit enter to apply changes to your local session' type='text' name='value' value='%s'></form>" % (str(item.key), str(item.value))})

    last_action = datetime.datetime.now().isoformat()
    action_list = dasmon.view_util.get_latest_updates(instrument_id,
                                                      message_channel=settings.SYSTEM_STATUS_PREFIX+'postprocessing')
    if len(action_list)>0:
        last_action = action_list[len(action_list)-1]['timestamp']

    # Breadcrumbs
    breadcrumbs =  "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (reverse('report.views.instrument_summary',args=[instrument]), instrument)
    breadcrumbs += " &rsaquo; configuration"

    template_values = {'instrument': instrument.upper(),
                       'helpline': settings.HELPLINE_EMAIL,
                       'params_list': params_list,
                       'action_list': action_list ,
                       'last_action_time': last_action,
                       'breadcrumbs': breadcrumbs}
    template_values.update(csrf(request))
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = dasmon.view_util.fill_template_values(request, **template_values)
    return render_to_response('reduction/configuration.html',
                              template_values)

@users.view_util.login_or_local_required
def configuration_cncs(request, instrument):
    """
        View current automated reduction configuration and modification history
        for a given instrument

        #TODO: redirect to another page if you are not part of the instrument team

        @param request: request object
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    default_extra = 0
    try:
        extra = int(request.GET.get('extra', default_extra))
    except:
        extra = default_extra
    MaskFormSet = formset_factory(forms.MaskForm, extra=extra)

    error_msg = []
    if request.method == 'POST':
        if "button_choice" not in request.POST:
            logging.error("Received incomplete POST request without a button_choice")
            return redirect(reverse('reduction.views.configuration', args=[instrument]))
        elif request.POST["button_choice"]=="reset":
            # Reset form parameters with default
            view_util.reset_to_default(instrument_id)
            return redirect(reverse('reduction.views.configuration', args=[instrument]))

        options_form = forms.ReductionConfigurationCNCSForm(request.POST)
        options_form.set_instrument(instrument.lower())
        mask_form = MaskFormSet(request.POST)
        if options_form.is_valid() and mask_form.is_valid():
            mask_block = forms.MaskForm.to_python(mask_form, indent='')
            options_form.cleaned_data['mask'] = mask_block
            options_form.to_db(instrument_id, request.user)
            # Send ActiveMQ request
            try:
                view_util.send_template_request(instrument_id, options_form.to_template(), user=request.user)
                return redirect(reverse('reduction.views.configuration', args=[instrument]))
            except:
                logging.error("Error sending AMQ script request: %s" % sys.exc_value)
                error_msg.append("Error processing request: %s" % sys.exc_value)
        else:
            logging.error("Invalid form %s %s" % (options_form.errors, mask_form.errors))
    else:
        params_dict = {}
        props_list = ReductionProperty.objects.filter(instrument=instrument_id)
        for item in props_list:
            params_dict[str(item.key)] = str(item.value)
        options_form = forms.ReductionConfigurationCNCSForm(initial=params_dict)
        options_form.set_instrument(instrument.lower())
        mask_list = []
        if 'mask' in params_dict:
            mask_list = forms.MaskForm.to_tokens(params_dict['mask'])
        mask_form = MaskFormSet(initial=mask_list)

    last_action = datetime.datetime.now().isoformat()
    action_list = dasmon.view_util.get_latest_updates(instrument_id,
                                                      message_channel=settings.SYSTEM_STATUS_PREFIX+'postprocessing')
    if len(action_list)>0:
        last_action = action_list[-1]['timestamp']
        action_list = action_list[-1:]

    # Breadcrumbs
    breadcrumbs =  "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (reverse('report.views.instrument_summary',args=[instrument]), instrument)
    breadcrumbs += " &rsaquo; configuration"

    template_values = {'instrument': instrument.upper(),
                       'helpline': settings.HELPLINE_EMAIL,
                       'options_form': options_form,
                       'mask_form': mask_form,
                       'action_list': action_list ,
                       'last_action_time': last_action,
                       'breadcrumbs': breadcrumbs,
                       'user_alert':error_msg}
    template_values.update(csrf(request))
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = dasmon.view_util.fill_template_values(request, **template_values)
    return render_to_response('reduction/configuration_cncs.html',
                              template_values)


@users.view_util.login_or_local_required
def configuration_dgs(request, instrument):
    """
        View current automated reduction configuration and modification history
        for a given instrument

        #TODO: redirect to another page if you are not part of the instrument team

        @param request: request object
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    default_extra = 0
    try:
        extra = int(request.GET.get('extra', default_extra))
    except:
        extra = default_extra
    MaskFormSet = formset_factory(forms.MaskForm, extra=extra)

    error_msg = []
    if request.method == 'POST':
        if "button_choice" not in request.POST:
            logging.error("Received incomplete POST request without a button_choice")
            return redirect(reverse('reduction.views.configuration', args=[instrument]))
        elif request.POST["button_choice"]=="reset":
            # Reset form parameters with default
            view_util.reset_to_default(instrument_id)
            return redirect(reverse('reduction.views.configuration', args=[instrument]))

        options_form = forms.ReductionConfigurationDGSForm(request.POST)
        options_form.set_instrument(instrument.lower())
        mask_form = MaskFormSet(request.POST)
        if options_form.is_valid() and mask_form.is_valid():
            mask_block = forms.MaskForm.to_python(mask_form)
            options_form.cleaned_data['mask'] = mask_block
            options_form.to_db(instrument_id, request.user)
            # Send ActiveMQ request
            try:
                view_util.send_template_request(instrument_id, options_form.to_template(), user=request.user)
                return redirect(reverse('reduction.views.configuration', args=[instrument]))
            except:
                logging.error("Error sending AMQ script request: %s" % sys.exc_value)
                error_msg.append("Error processing request: %s" % sys.exc_value)
        else:
            logging.error("Invalid form %s %s" % (options_form.errors, mask_form.errors))
    else:
        params_dict = {}
        props_list = ReductionProperty.objects.filter(instrument=instrument_id)
        for item in props_list:
            params_dict[str(item.key)] = str(item.value)
        options_form = forms.ReductionConfigurationDGSForm(initial=params_dict)
        options_form.set_instrument(instrument.lower())
        mask_list = []
        if 'mask' in params_dict:
            mask_list = forms.MaskForm.to_tokens(params_dict['mask'])
        mask_form = MaskFormSet(initial=mask_list)

    last_action = datetime.datetime.now().isoformat()
    action_list = dasmon.view_util.get_latest_updates(instrument_id,
                                                      message_channel=settings.SYSTEM_STATUS_PREFIX+'postprocessing')
    if len(action_list)>0:
        last_action = action_list[-1]['timestamp']
        action_list = action_list[-1:]

    # Breadcrumbs
    breadcrumbs =  "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (reverse('report.views.instrument_summary',args=[instrument]), instrument)
    breadcrumbs += " &rsaquo; configuration"

    template_values = {'instrument': instrument.upper(),
                       'helpline': settings.HELPLINE_EMAIL,
                       'options_form': options_form,
                       'mask_form': mask_form,
                       'action_list': action_list ,
                       'last_action_time': last_action,
                       'breadcrumbs': breadcrumbs,
                       'user_alert':error_msg}
    template_values.update(csrf(request))
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = dasmon.view_util.fill_template_values(request, **template_values)
    return render_to_response('reduction/configuration_dgs.html',
                              template_values)

@users.view_util.login_or_local_required
def configuration_corelli(request, instrument):
    """
        View current automated reduction configuration and modification history
        for a given instrument

        #TODO: redirect to another page if you are not part of the instrument team

        @param request: request object
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())

    default_extra = 0
    try:
        extra_mask = int(request.GET.get('extra_mask', default_extra))
    except:
        extra_mask = default_extra
    try:
        extra_orientation = int(request.GET.get('extra_orientation', default_extra))
    except:
        extra_orientation = default_extra
    MaskFormSet = formset_factory(forms.MaskForm, extra=extra_mask)
    PlotFormSet = formset_factory(forms.PlottingForm, extra=extra_orientation)

    error_msg = []
    if request.method == 'POST':
        if "button_choice" not in request.POST:
            logging.error("Received incomplete POST request without a button_choice")
            return redirect(reverse('reduction.views.configuration', args=[instrument]))
        elif request.POST["button_choice"]=="reset":
            # Reset form parameters with default
            view_util.reset_to_default(instrument_id)
            return redirect(reverse('reduction.views.configuration', args=[instrument]))

        options_form = forms.ReductionConfigurationCorelliForm(request.POST)
        mask_form = MaskFormSet(request.POST)
        plot_form = PlotFormSet(request.POST)
        if options_form.is_valid() and mask_form.is_valid() and plot_form.is_valid():
            mask_block = forms.MaskForm.to_dict_list(mask_form)
            options_form.cleaned_data['mask'] = str(mask_block)
            plot_block = forms.PlottingForm.to_dict_list(plot_form)
            options_form.cleaned_data['plot_requests'] = str(plot_block)
            options_form.to_db(instrument_id, request.user)
            # Send ActiveMQ request
            try:
                view_util.send_template_request(instrument_id, options_form.to_template(), user=request.user)
                return redirect(reverse('reduction.views.configuration', args=[instrument]))
            except:
                logging.error("Error sending AMQ script request: %s" % sys.exc_value)
                error_msg.append("Error processing request: %s" % sys.exc_value)
        else:
            logging.error("Invalid form %s %s" % (options_form.errors, mask_form.errors))
    else:
        params_dict = {}
        props_list = ReductionProperty.objects.filter(instrument=instrument_id)
        for item in props_list:
            params_dict[str(item.key)] = str(item.value)
        options_form = forms.ReductionConfigurationCorelliForm(initial=params_dict)
        mask_list = []
        plot_list = []
        if 'mask' in params_dict:
            try:
                mask_list = forms.MaskForm.from_dict_list(params_dict['mask'])
            except:
                logging.error("Error evaluating the mask information: %s" % sys.exc_value)
        if 'plot_requests' in params_dict:
            try:
                plot_list = forms.PlottingForm.from_dict_list(params_dict['plot_requests'])
            except:
                logging.error("Error evaluating the plotting information: %s" % sys.exc_value)
        mask_form = MaskFormSet(initial=mask_list)
        plot_form = PlotFormSet(initial=plot_list)

    last_action = datetime.datetime.now().isoformat()
    action_list = dasmon.view_util.get_latest_updates(instrument_id,
                                                      message_channel=settings.SYSTEM_STATUS_PREFIX+'postprocessing')
    if len(action_list)>0:
        last_action = action_list[-1]['timestamp']
        action_list = action_list[-1:]

    # Breadcrumbs
    breadcrumbs =  "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s</a>" % (reverse('report.views.instrument_summary',args=[instrument]), instrument)
    breadcrumbs += " &rsaquo; configuration"

    template_values = {'instrument': instrument.upper(),
                       'helpline': settings.HELPLINE_EMAIL,
                       'options_form': options_form,
                       'mask_form': mask_form,
                       'plot_form': plot_form,
                       'action_list': action_list ,
                       'last_action_time': last_action,
                       'breadcrumbs': breadcrumbs,
                       'user_alert':error_msg}
    template_values.update(csrf(request))
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = dasmon.view_util.fill_template_values(request, **template_values)
    return render_to_response('reduction/configuration_corelli.html',
                              template_values)

@csrf_exempt
@users.view_util.login_or_local_required_401
def configuration_change(request, instrument):
    """
        AJAX call to update the reduction parameters for an instrument.

        @param request: request object
        @param instrument: instrument name
    """
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    if 'data' in request.POST:
        template_data = json.loads(request.POST['data'])
        template_dict = {}
        for item in template_data:
            try:
                template_dict[item['key']] = item['value']
                view_util.store_property(instrument_id, item['key'], item['value'], user=request.user)
            except:
                logging.error("config_change: %s" % sys.exc_value)

        # Check whether the user wants to install the default script
        if 'use_default' in request.POST:
            try:
                template_dict['use_default'] = int(request.POST['use_default'])==1
            except:
                logging.error("Error parsing use_default parameter: %s" % sys.exc_value)
        # Send ActiveMQ request
        try:
            view_util.send_template_request(instrument_id, template_dict, user=request.user)
        except:
            logging.error("Error sending AMQ script request: %s" % sys.exc_value)
            return HttpResponse("Error processing request", status=500)

    data_dict = {}
    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response

@users.view_util.login_or_local_required_401
#@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def configuration_update(request, instrument):
    """
        AJAX call that returns an updated list of recent actions taken
        on the reduction script for the specified instrument.

        @param request: request object
        @param instrument: instrument name
    """
    last_action = request.GET.get('since', '0')
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    action_list = []
    if last_action is not '0':
        start_time = dateparse.parse_datetime(last_action)
        start_time = timezone.make_aware(start_time, timezone.utc)
        action_list = dasmon.view_util.get_latest_updates(instrument_id,
                                                          message_channel=settings.SYSTEM_STATUS_PREFIX+'postprocessing',
                                                          start_time=start_time)
    data_dict = {'last_action_time': last_action, 'refresh_needed': '0'}
    if len(action_list)>0:
        data_dict['last_action_time'] = action_list[len(action_list)-1]['timestamp']
        data_dict['refresh_needed'] = '1'
    data_dict['actions'] = action_list
    response = HttpResponse(json.dumps(data_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response