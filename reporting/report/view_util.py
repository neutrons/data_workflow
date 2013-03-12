from report.models import DataRun, RunStatus, WorkflowSummary, IPTS, Instrument, Error
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils import simplejson, dateformat, timezone
import datetime
from django.conf import settings

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
    last_run_id = DataRun.objects.get_last_run(instrument_id)
    if last_run_id is None:
        last_expt_id = IPTS.objects.get_last_ipts(instrument_id)
    else:
        last_expt_id = last_run_id.ipts_id
    template_args['last_expt'] = last_expt_id
    template_args['last_run'] = last_run_id   

    # Get base IPTS URL
    base_ipts_url = reverse('report.views.ipts_summary',args=[instr,'0000'])
    base_ipts_url = base_ipts_url.replace('/0000','')
    template_args['base_ipts_url'] = base_ipts_url
    
    # Get base Run URL
    base_run_url = reverse('report.views.detail',args=[instr,'0000'])
    base_run_url = base_run_url.replace('/0000','')
    template_args['base_run_url'] = base_run_url
    
    # Get run rate and error rate
    r_rate = run_rate(instrument_id)
    e_rate = error_rate(instrument_id)
    template_args['run_rate'] = str(r_rate)
    template_args['error_rate'] = str(e_rate)
                       
    return template_args

class DataSorter(object):
    """
        Sorter object to organize data in a sorted grid
    """
    ## Sort item query string
    SORT_ITEM_QUERY_STRING = 'ds'
    ## Sort direction query string
    SORT_DIRECTION_QUERY_STRING = 'dd'
    
    # Sort direction information
    KEY_ASC     = 'asc'
    KEY_DESC    = 'desc'
    DEFAULT_DIR = KEY_DESC
    DIR_CHOICES = [KEY_ASC, KEY_DESC]
    
    # Sort item
    KEY_MOD     = 'time'
    KEY_NAME    = 'name'
    DEFAULT_ITEM = KEY_MOD
    ITEM_CHOICES = [KEY_MOD, KEY_NAME]
    COLUMN_DICT = {KEY_MOD: 'time',
                   KEY_NAME: 'name'}
    
    def __init__(self, request):
        """
            Initialize the sorting parameters
            @param request: get the sorting information from the HTTP request
        """
        # Get the default from the user session
        #default_dir = request.session.get(self.SORT_DIRECTION_QUERY_STRING, default=self.DEFAULT_DIR)
        #default_item = request.session.get(self.SORT_ITEM_QUERY_STRING, default=self.DEFAULT_ITEM)
        
        # Get the sorting options from the query parameters
        self.sort_dir = request.GET.get(self.SORT_DIRECTION_QUERY_STRING, self.DEFAULT_DIR)
        self.sort_key = request.GET.get(self.SORT_ITEM_QUERY_STRING, self.DEFAULT_ITEM)
        
        # Clean up sort direction
        self.sort_dir = self.sort_dir.lower().strip()
        if self.sort_dir not in self.DIR_CHOICES:
            self.sort_dir = self.DEFAULT_DIR
        
        # Clean up sort column
        self.sort_key = self.sort_key.lower().strip()
        if self.sort_key not in self.ITEM_CHOICES:
            self.sort_key = self.DEFAULT_ITEM        
        self.sort_item = self.COLUMN_DICT[self.sort_key]
        
        # Store sorting parameters in session
        #request.session[self.SORT_DIRECTION_QUERY_STRING] = self.sort_dir
        #request.session[self.SORT_ITEM_QUERY_STRING] = self.sort_item
        
        ## User ID
        self.user = request.user

    def _create_header_dict(self, long_name, url_name, min_width=None):
        """
            Creates column header, the following classes have to
            be define in the CSS style sheet

            "sorted descending"
            "sorted ascending"
            
            @param long_name: name that will appear in the table header
            @param url_name: URL query field
        """
        if url_name is None:
            url = None
        else:
            url = "?%s=%s&amp;%s=%s" % (self.SORT_DIRECTION_QUERY_STRING,
                                        self.KEY_ASC, self.SORT_ITEM_QUERY_STRING, url_name)
            
        d = {'name': long_name,
             'url': url}
        if self.sort_key == url_name:
            if self.sort_dir == self.KEY_DESC:
                d['class'] = "sorted descending"
            else:
                d['class'] = "sorted ascending"
                if url_name is None:
                    url = None
                else:
                    url = "?%s=%s&amp;%s=%s" % (self.SORT_DIRECTION_QUERY_STRING, 
                                                 self.KEY_DESC, self.SORT_ITEM_QUERY_STRING, url_name)
                d['url'] = url
                
        if min_width is not None:
            d['style'] = "min-width: %dpx;" % min_width
        return d

    def __call__(self, instrument_id=None): return NotImplemented
    def _retrieve_data(self, instrument_id): return NotImplemented
    

class ExperimentSorter(DataSorter):
    """
        Sorter object to organize data in a sorted grid
    """
    # Sort item
    KEY_MOD     = 'time'
    KEY_NAME    = 'name'
    DEFAULT_ITEM = KEY_MOD
    ITEM_CHOICES = [KEY_MOD, KEY_NAME]
    COLUMN_DICT = {KEY_MOD: 'created_on',
                   KEY_NAME: 'expt_name'}

            
    def __call__(self, instrument_id):
        """
            Returns the data and header to populate a data grid
        """
        # Query the database
        data = self._retrieve_data(instrument_id)
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("Experiment", self.KEY_NAME, min_width=80))
        header.append(self._create_header_dict("No. of runs", None, min_width=50))
        header.append(self._create_header_dict("Created on", self.KEY_MOD))
        
        return data, header
    
    def _retrieve_data(self, instrument_id): 
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            return IPTS.objects.filter(instruments=instrument_id).order_by(self.sort_item).reverse()
        else:
            return IPTS.objects.filter(instruments=instrument_id).order_by(self.sort_item)

        
class RunSorter(DataSorter):
    # Sort item
    KEY_MOD     = 'time'
    KEY_NAME    = 'run'
    DEFAULT_ITEM = KEY_MOD
    ITEM_CHOICES = [KEY_MOD, KEY_NAME]
    COLUMN_DICT = {KEY_MOD: 'created_on',
                   KEY_NAME: 'run_number'}
    N_RECENT = 20
            
    def __call__(self, ipts_id, show_all=False, n_shown=20):
        """
            Returns the data and header to populate a data grid
        """
        self.N_RECENT = n_shown
        # Query the database
        data = self._retrieve_data(ipts_id, show_all=show_all)
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("Run", self.KEY_NAME, min_width=50))
        header.append(self._create_header_dict("Created on", self.KEY_MOD))
        header.append(self._create_header_dict("Last known error", None))
        
        return data, header
    
    def _retrieve_data(self, ipts_id, show_all=False): 
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            runs = DataRun.objects.filter(ipts_id=ipts_id).order_by(self.sort_item).reverse()
        else:
            runs = DataRun.objects.filter(ipts_id=ipts_id).order_by(self.sort_item)
        if not show_all and len(runs)>self.N_RECENT:
            return runs[:self.N_RECENT]
        return runs

class ActivitySorter(DataSorter):
    # Sort item
    KEY_MOD     = 'time'
    KEY_NAME    = 'name'
    DEFAULT_ITEM = KEY_MOD
    ITEM_CHOICES = [KEY_MOD, KEY_NAME]
    COLUMN_DICT = {KEY_MOD: 'created_on',
                   KEY_NAME: 'name'}
            
    def __call__(self, run_id):
        """
            Returns the data and header to populate a data grid
        """
        # Query the database
        data = self._retrieve_data(run_id)
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("Message", None))
        header.append(self._create_header_dict("Information", None))
        header.append(self._create_header_dict("Time", self.KEY_MOD))
        
        return data, header
    
    def _retrieve_data(self, run_id): 
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            return RunStatus.objects.filter(run_id=run_id).order_by(self.sort_item).reverse()
        else:
            return RunStatus.objects.filter(run_id=run_id).order_by(self.sort_item)

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
        header.append(self._create_header_dict("Experiment", None, min_width=80))
        header.append(self._create_header_dict("Run", self.KEY_NAME, min_width=50))
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

