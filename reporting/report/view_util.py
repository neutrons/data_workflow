from report.models import DataRun, RunStatus, WorkflowSummary, IPTS, Instrument

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
        default_dir = request.session.get(self.SORT_DIRECTION_QUERY_STRING, default=self.DEFAULT_DIR)
        default_item = request.session.get(self.SORT_ITEM_QUERY_STRING, default=self.DEFAULT_ITEM)
        
        # Get the sorting options from the query parameters
        self.sort_dir = request.GET.get(self.SORT_DIRECTION_QUERY_STRING, default_dir)
        self.sort_key = request.GET.get(self.SORT_ITEM_QUERY_STRING, default_item)
        
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
        request.session[self.SORT_DIRECTION_QUERY_STRING] = self.sort_dir
        request.session[self.SORT_ITEM_QUERY_STRING] = self.sort_item
        
        ## User ID
        self.user = request.user

    def _create_header_dict(self, long_name, url_name):
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
        header.append(self._create_header_dict("Experiment", self.KEY_NAME))
        header.append(self._create_header_dict("Number of runs", None))
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
            
    def __call__(self, ipts_id, show_all=False):
        """
            Returns the data and header to populate a data grid
        """
        # Query the database
        data = self._retrieve_data(ipts_id, show_all=show_all)
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("Run number", self.KEY_NAME))
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
        header.append(self._create_header_dict("Time", self.KEY_MOD))
        header.append(self._create_header_dict("Message", None))
        header.append(self._create_header_dict("Information", None))
        
        return data, header
    
    def _retrieve_data(self, run_id): 
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            return RunStatus.objects.filter(run_id=run_id).order_by(self.sort_item).reverse()
        else:
            return RunStatus.objects.filter(run_id=run_id).order_by(self.sort_item)

    