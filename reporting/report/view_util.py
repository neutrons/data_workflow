from report.models import DataRun, RunStatus, WorkflowSummary, IPTS, Instrument, Error, StatusQueue, Task
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils import simplejson, dateformat, timezone
import datetime
from django.conf import settings
import logging
import sys
from django.db import connection

import dasmon.view_util

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
    
    template_args = dasmon.view_util.fill_template_values(request, **template_args)

    return template_args

def needs_reduction(request, run_id):
    """
        Determine whether we need a reduction link to 
        submit a run for automated reduction
        @param request: HTTP request object
        @param run_id: DataRun object
    """
    # Verify that user is allowed to launch a job
    try:
        instr_group = Group.objects.get(name="InstrumentTeam")
    except Group.DoesNotExist:
        return False

    if not instr_group in request.user.groups.all() \
        and request.user.is_staff is False:
        return False
    
    # Get REDUCTION.DATA_READY queue
    try:
        red_queue = StatusQueue.objects.get(name="REDUCTION.DATA_READY")
    except StatusQueue.DoesNotExist:
        logging.error(sys.exc_value)
        return False

    # Check whether we have a task for this queue    
    tasks = Task.objects.filter(instrument_id=run_id.instrument_id,
                                input_queue_id=red_queue)
    if len(tasks)==1 and \
        (tasks[0].task_class is None or len(tasks[0].task_class)==0) \
        and len(tasks[0].task_queue_ids.all())==0:
            return False
       
    return True
    
    
def send_reduction_request(instrument_id, run_id):
    """
        Send an AMQ message to the workflow manager to reprocess
        the run
        @param instrument_id: Instrument object
        @param run_id: DataRun object
    """
    from workflow.settings import brokers, icat_user, icat_passcode
    import stomp
    import json
    # Build up dictionary
    data_dict = {'facility': 'SNS',
                 'instrument': str(instrument_id),
                 'ipts': run_id.ipts_id.expt_name.upper(),
                 'run_number': run_id.run_number,
                 'data_file': run_id.file
                 }
    data = json.dumps(data_dict)
    conn = stomp.Connection(host_and_ports=brokers, 
                            user=icat_user, 
                            passcode=icat_passcode, 
                            wait_on_receipt=True)
    conn.start()
    conn.connect()
    conn.send(destination='/queue/POSTPROCESS.DATA_READY', message=data, persistent='true')
    conn.disconnect()
    logging.info("Reduction requested: %s" % str(data))
        
        
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
            
    def __call__(self, ipts_id, show_all=False, n_shown=20, instrument_id=None):
        """
            Returns the data and header to populate a data grid
        """
        self.N_RECENT = n_shown
        # Query the database
        data = self._retrieve_data(ipts_id, show_all=show_all, instrument_id=instrument_id)
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("Run", self.KEY_NAME, min_width=50))
        header.append(self._create_header_dict("Created on", self.KEY_MOD))
        header.append(self._create_header_dict("Status", None))
        
        return data, header
    
    def _retrieve_data(self, ipts_id, show_all=False, instrument_id=None): 
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            if instrument_id is None:
                runs = DataRun.objects.filter(ipts_id=ipts_id).order_by(self.sort_item).reverse()
            else:
                runs = DataRun.objects.filter(ipts_id=ipts_id, instrument_id=instrument_id).order_by(self.sort_item).reverse()
        else:
            if instrument_id is None:
                runs = DataRun.objects.filter(ipts_id=ipts_id).order_by(self.sort_item)
            else:
                runs = DataRun.objects.filter(ipts_id=ipts_id, instrument_id=instrument_id).order_by(self.sort_item)
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
    # Try calling the stored procedure (faster)
    try:
        cursor = connection.cursor()
        cursor.callproc("run_rate", (instrument_id.id,))
        msg = cursor.fetchone()[0]
        cursor.execute('FETCH ALL IN "%s"' % msg)
        rows = cursor.fetchall()
        cursor.close()
        return [ [int(r[0]), int(r[1])] for r in rows ]
    except:
        connection.close()
        logging.error(sys.exc_value)
        
        # Do it by hand (slow)
        time = timezone.now()
        runs=[]
        running_sum = 0
        for i in range(n_hours):
            t_i = time-datetime.timedelta(hours=i+1)
            n = DataRun.objects.filter(instrument_id=instrument_id, created_on__gte=t_i).count()
            n -= running_sum
            running_sum += n
            runs.append([-i,n])
        return runs

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
        return [ [int(r[0]), int(r[1])] for r in rows ]
    except:
        connection.close()
        logging.error(sys.exc_value)
        
        # Do it by hand (slow)
        time = timezone.now()
        errors=[]
        running_sum = 0
        for i in range(n_hours):
            t_i = time-datetime.timedelta(hours=i+1)
            n = Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id, run_status_id__created_on__gte=t_i).count()
            n -= running_sum
            running_sum += n
            errors.append([-i,n])
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
    data_dict = {
                 'run_rate':r_rate,
                 'error_rate':e_rate,
                 }
    
    if last_run_id is not None:
        localtime = timezone.localtime(last_run_id.created_on)
        df = dateformat.DateFormat(localtime)
        data_dict['last_run_id']=last_run_id.id
        data_dict['last_run']=last_run_id.run_number
        data_dict['last_run_time']=df.format(settings.DATETIME_FORMAT)
    
    if last_expt_id is not None:
        data_dict['last_expt_id']=last_expt_id.id
        data_dict['last_expt']=last_expt_id.expt_name.upper()

    return data_dict

def get_post_processing_status(red_timeout=0.25, yellow_timeout=10):
    """
        Get the health status of post-processing services
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    status_dict = {}
    delta_short = datetime.timedelta(seconds=yellow_timeout)
    delta_long = datetime.timedelta(hours=red_timeout)
 
    try:
        # Get latest DATA_READY message
        postprocess_data_id = StatusQueue.objects.get(name='POSTPROCESS.DATA_READY')
        catalog_data_id = StatusQueue.objects.get(name='CATALOG.DATA_READY')
        catalog_start_id = StatusQueue.objects.get(name='CATALOG.STARTED')
        reduction_start_id = StatusQueue.objects.get(name='REDUCTION.STARTED')
        latest_run = RunStatus.objects.filter(queue_id=postprocess_data_id).latest('created_on')
        
        # If we didn't get a CATALOG.STARTED message within a few seconds, 
        # the cataloging agent has a problem
        try:
            latest_catalog_start = RunStatus.objects.filter(queue_id=catalog_start_id,
                                                            run_id=latest_run.run_id).latest('created_on')
            time_catalog_start = latest_catalog_start.created_on
        except:
            time_catalog_start = timezone.now()
                
        if time_catalog_start-latest_run.created_on>delta_long:
            status_dict["catalog"]=2
        elif time_catalog_start-latest_run.created_on>delta_short:
            status_dict["catalog"]=1
        else:
            status_dict["catalog"]=0

        # If we didn't get a REDUCTION.STARTED message within a few seconds, 
        # the cataloging agent has a problem
        try:
            latest_reduction_start = RunStatus.objects.filter(queue_id=reduction_start_id,
                                                            run_id=latest_run.run_id).latest('created_on')
            time_reduction_start = latest_reduction_start.created_on
        except:
            time_reduction_start = timezone.now()
                
        if time_reduction_start-latest_run.created_on>delta_long:
            status_dict["reduction"]=2
        elif time_reduction_start-latest_run.created_on>delta_short:
            status_dict["reduction"]=1
        else:
            status_dict["reduction"]=0               
    except:
        logging.error("Could not determine post-processing status")
        logging.error(sys.exc_value)
    
    return status_dict
    
    
    
    