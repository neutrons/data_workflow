#pylint: disable=invalid-name, line-too-long, too-many-branches
"""
    Forms for auto-reduction configuration

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2016 Oak Ridge National Laboratory
"""
import sys
from django import forms
from django.core.exceptions import ValidationError
from report.models import Instrument, IPTS, DataRun, StatusQueue
from dasmon.models import ActiveInstrument
import logging
from report.icat_server_communication import get_run_info

def validate_integer_list(value):
    """
        Allow for "1,2,3" and "1-3"

        @param value: string value to parse
    """
    value_list = []
    # Look for a list of ranges
    for item in value.split(','):
        if '-' in item:
            range_toks = item.split('-')
            if len(range_toks) == 2:
                try:
                    value_list.extend(range(int(range_toks[0]), int(range_toks[1])+1))
                except:
                    logging.error(sys.exc_value)
                    raise ValidationError(u'Error parsing %s for a range of integers' % value)
            else:
                logging.error("Found more than two tokens around -")
                raise ValidationError(u'Error parsing %s for a range of integers' % value)

        else:
            try:
                value_list.append(int(item))
            except:
                logging.error(sys.exc_value)
                raise ValidationError(u'Error parsing %s for a range of integers' % value)

    return value_list

class ProcessingForm(forms.Form):
    """
        Form to send a post-processing request
    """
    instrument = forms.ChoiceField(required=True, choices=[])
    experiment = forms.CharField(required=True, initial='')
    run_list = forms.CharField(required=True, initial='', validators=[validate_integer_list])
    create_as_needed = forms.BooleanField(required=False, initial=False)
    task = forms.ChoiceField(required=True, choices=[])

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

    def set_initial(self, initial):
        """
            Set the initial values after cleaning them up
            @param initial: initial dictionary
        """
        self.initial = {}
        if 'instrument' in initial:
            self.initial['instrument'] = initial['instrument']
        else:
            self.initial['instrument'] = self.fields['instrument'].choices[0]

        if 'experiment' in initial:
            self.initial['experiment'] = initial['experiment']

        if 'run_list' in initial:
            self.initial['run_list'] = initial['run_list']

        if 'task' in initial:
            self.initial['task'] = initial['task']
        else:
            self.initial['task'] = "POSTPROCESS.DATA_READY"

        if 'create_as_needed' in initial:
            self.initial['create_as_needed'] = self.fields['create_as_needed'].to_python(initial['create_as_needed'])

    def process(self):
        """
            Process the completed form
        """
        output_report = ""
        # Retrieve the instrument
        try:
            instrument = Instrument.objects.get(name=self.cleaned_data['instrument'])
            output_report += "Found instrument %s<br>" % str(instrument)
        except Instrument.DoesNotExist:
            output_report += "Could not find instrument %s<br>" % self.cleaned_data['instrument']
            output_report += "Fix your inputs and re-submit<br>"
            return {'report': output_report, 'task': None}

        # Special recovery process
        if self.cleaned_data['experiment'].upper() == "FIND" and self.cleaned_data['create_as_needed']:
            return self._recover_processed_run(instrument)

        # Verify that the experiment exists
        try:
            ipts = IPTS.objects.get(instruments=instrument,
                                    expt_name=self.cleaned_data['experiment'].upper())
            output_report += "Found experiment %s<br>" % str(ipts)
        except IPTS.DoesNotExist:
            output_report += "Could not find experiment %s<br>" % self.cleaned_data['experiment']
            output_report += "Fix your inputs and re-submit<br>"
            return {'report': output_report, 'task': None}

        # Parse the runs and make sure they all exist
        run_list = validate_integer_list(self.cleaned_data['run_list'])
        invalid_runs = []
        valid_run_objects = []
        for run in run_list:
            try:
                run_obj = DataRun.objects.get(instrument_id=instrument,
                                              ipts_id = ipts,
                                              run_number=run)
                valid_run_objects.append(run_obj)
            except DataRun.DoesNotExist:
                invalid_runs.append(run)
                if self.cleaned_data['create_as_needed']:
                    # Create a file path
                    if not ActiveInstrument.objects.is_adara(instrument):
                        file_path = "/SNS/%s/%s/0/%s/NeXus/%s_%r_event.nxs" % \
                        (str(instrument).upper(), ipts, run, str(instrument).upper(), run)
                    else:
                        base_path = "/SNS/%s/%s/nexus/" % (str(instrument).upper(), ipts)
                        file_path = "%s/%s_%s.nxs.h5" % (base_path, str(instrument).upper(), run)
                    new_run = type('new_run', (object,), {'instrument_id' : instrument,
                                                          'run_number': run,
                                                          'ipts_id': ipts,
                                                          'file': file_path})
                    valid_run_objects.append(new_run)
        if len(invalid_runs) == 0:
            output_report += "All the runs were valid<br>"
        else:
            # First look for mismatch between run and ipts
            has_ipts_mismatch = False
            for run in invalid_runs:
                run_list = DataRun.objects.filter(instrument_id=instrument, run_number=run)
                if len(run_list)>0:
                    output_report += "Run %s was found in experiment %s<br>" % (run, run_list[0].ipts_id)
                    has_ipts_mismatch = True

            if has_ipts_mismatch:
                output_report += "Fix your inputs and re-submit<br>"
                return {'report': output_report, 'task': None}

            if self.cleaned_data['create_as_needed']:
                output_report += "The following runs will be created: %s<br>" % str(invalid_runs)
            else:
                output_report += "The following were invalid runs: %s<br>" % str(invalid_runs)
                output_report += "Fix your inputs and re-submit<br>"
                return {'report': output_report, 'task': None}

        # Retrieve the command
        try:
            queue = StatusQueue.objects.get(name=self.cleaned_data['task'])
        except StatusQueue.DoesNotExist:
            logging.error(sys.exc_value)

        # Returns a report and task to be sent
        return {'report': output_report, 'task': str(queue),
                'instrument': instrument, 'runs': valid_run_objects}

    def _recover_processed_run(self, instrument):
        """
            Recovery method for when runs exist in ICAT but need to be inserted into the workflow DB
        """
        # Parse the runs and make sure they all exist
        run_list = validate_integer_list(self.cleaned_data['run_list'])
        valid_run_objects = []
        for run in run_list:
            new_run = type('new_run', (object,), {'instrument_id' : instrument,
                                                  'run_number': run,
                                                  'ipts_id': '',
                                                  'file': ''})
            valid_run_objects.append(new_run)

        output_report = "Your runs will be created if they exist in ICAT<br>"

        # Returns a report and task to be sent
        return {'report': output_report, 'task': str(self.cleaned_data['task']).upper(),
                'instrument': instrument, 'runs': valid_run_objects, 'is_complete': True}
