from report.view_util import DataSorter
from report.models import DataRun, RunStatus, IPTS, Instrument, Error

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

       