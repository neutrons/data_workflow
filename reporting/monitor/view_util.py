from report.view_util import DataSorter
from report.models import DataRun, RunStatus, IPTS, Instrument, Error
import datetime
from django.utils import dateformat, timezone
from django.conf import settings

class ErrorSorter(DataSorter):
    """
        Sorter object to organize data in a sorted grid
    """
    # Sort item
    KEY_MOD     = 'time'
    KEY_NAME    = 'name'
    DEFAULT_ITEM = KEY_MOD
    ITEM_CHOICES = [KEY_MOD, KEY_NAME]
    COLUMN_DICT = {KEY_MOD: 'run_status_id__created_on',
                   KEY_NAME: 'run_status_id__run_id__run_number'}
            
    def __call__(self, instrument_id):
        """
            Returns the data and header to populate a data grid
        """
        # Query the database
        data = self._retrieve_data(instrument_id)
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("Experiment", None, min_width=90))
        header.append(self._create_header_dict("Run number", self.KEY_NAME, min_width=90))
        header.append(self._create_header_dict("Error", None))
        header.append(self._create_header_dict("Time", self.KEY_MOD))
        
        return data, header
    
    def _retrieve_data(self, instrument_id): 
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            return Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id).order_by(self.sort_item).reverse()
        else:
            return Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id).order_by(self.sort_item)

       
def run_rate(instrument_id, n_hours=24):
    """
        Returns the rate of new runs for the last n_hours hours.
        @param instrument_id: Instrument model object
        @param n_hours: number of hours to track
    """
    time = timezone.now()
    runs=[]
    running_sum = 0
    for i in range(n_hours):
        t_i = time-datetime.timedelta(hours=i+1)
        n = DataRun.objects.filter(instrument_id=instrument_id, created_on__gte=t_i).count()
        n -= running_sum
        running_sum += n
        runs.append([n_hours-i,n])
    return runs

def error_rate(instrument_id, n_hours=24):
    """
        Returns the rate of errors for the last n_hours hours.
        @param instrument_id: Instrument model object
        @param n_hours: number of hours to track
    """
    time = timezone.now()
    errors=[]
    running_sum = 0
    for i in range(n_hours):
        t_i = time-datetime.timedelta(hours=i+1)
        n = Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id, run_status_id__created_on__gte=t_i).count()
        n -= running_sum
        running_sum += n
        errors.append([n_hours-i,n])
    return errors
        
def get_current_status(instrument_id):
    """
        Get current status information such as the last
        experiment/run for a given instrument
        @param instrument_id: Instrument model object
    """
    # Get last experiment and last run
    last_run_id = DataRun.objects.get_last_run(instrument_id)
    if last_run_id is None:
        last_expt_id = IPTS.objects.get_last_ipts(instrument_id)
    else:
        last_expt_id = last_run_id.ipts_id

    r_rate = run_rate(instrument_id)
    e_rate = error_rate(instrument_id)
    
    localtime = timezone.localtime(last_run_id.created_on)
    df = dateformat.DateFormat(localtime)
    
    data_dict = {
                 'last_expt_id':last_expt_id.id,
                 'last_expt':last_expt_id.expt_name.upper(),
                 'last_run_id':last_run_id.id,
                 'last_run':last_run_id.run_number,
                 'last_run_time':df.format(settings.DATETIME_FORMAT),
                 'run_rate':r_rate,
                 'error_rate':e_rate,
                 }
    return data_dict

