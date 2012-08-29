"""
    Live monitoring
"""
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from report.views import confirm_instrument
from monitor.models import Parameter, ReportedValue
from report.models import Instrument

import time

def generate(instrument, parameter):
    import datetime
    import math
    
    for i in range(59):
        t = datetime.datetime(2012,8,24,16,i,i)
        v = ReportedValue(instrument_id=instrument,
                          parameter_id=parameter,
                          value = 150.0+10.0*math.sin(i/10.0),
                          timestamp=t)
        v.save()

@confirm_instrument
def live_instrument(request, instrument):
    
    return render_to_response('monitor/live_instrument.html', {'instrument': instrument})
    
@confirm_instrument
def live_parameter(request, instrument, parameter):
    
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    parameter_id = get_object_or_404(Parameter, name=parameter.lower())
    
    values = ReportedValue.objects.filter(instrument_id=instrument_id,
                                           parameter_id=parameter_id).order_by('timestamp')
    
    #generate(instrument_id, parameter_id)
    
    points = []
    for pt in values:
        points.append([time.mktime(pt.timestamp.timetuple()), float(pt.value), 10.0])
    
    # Breadcrumbs
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse('report.views.summary'),
            reverse('report.views.instrument_summary',args=[instrument]), instrument,
            parameter.lower()
            ) 
    
    # Get base URL
    base_url = reverse('monitor.views.live_parameter',args=[instrument, '0000'])
    base_url = base_url.replace('/0000','')
    
    # Get list of available parameters
    parameter_list = Parameter.objects.distinct().values_list('name', flat=True).order_by('name')
    
    parameter = parameter.capitalize()
    
    return render_to_response('monitor/live_parameter.html', {'instrument': instrument,
                                                              'parameter': parameter,
                                                              'breadcrumbs': breadcrumbs,
                                                              'parameter_list':parameter_list,
                                                              'base_monitor_url':base_url,
                                                              'points': points})
