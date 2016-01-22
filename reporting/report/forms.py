"""
    Forms for auto-reduction configuration
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2016 Oak Ridge National Laboratory
"""
from django import forms
from django.core.exceptions import ValidationError
from report.models import Instrument, StatusQueue
from dasmon.models import ActiveInstrument

def validate_integer_list(value):
    """
        Allow for "1,2,3" and "1-3"

        @param value: string value to parse
    """
    # Look for a list of ranges
    range_list = value.split(',')
    for item in range_list:
        for item in item.split('-'):
            try:
                int(item.strip())
            except:
                raise ValidationError(u'Error parsing %s for a range of integers' % value)

class ProcessingForm(forms.Form):
    """
        Form to send a post-processing request
    """
    instrument = forms.ChoiceField(required=True, choices=[])
    experiment = forms.CharField(required=False, initial='')
    run_list = forms.CharField(required=False, initial='', validators=[validate_integer_list])
    task = forms.ChoiceField(required=False, choices=[])

    def __init__(self, *args, **kwargs):
        super(ProcessingForm, self).__init__(*args, **kwargs)
        
        # Get the list of available instruments
        instruments = [ (str(i), str(i)) for i in Instrument.objects.all().order_by('name') if ActiveInstrument.objects.is_alive(i) ]
        self.fields['instrument'].choices = instruments
        
        # Get the list of available inputs
        queue_ids = StatusQueue.objects.filter(is_workflow_input=True)
        tasks = [ (str(q), str(q)) for q in queue_ids if (str(q).endswith('REQUEST') or \
                                                          str(q).endswith('DATA_READY') or \
                                                          str(q).endswith('NOT_NEEDED'))]
        self.fields['task'].choices = tasks
