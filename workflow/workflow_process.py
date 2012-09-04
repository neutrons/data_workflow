"""
    Actual process that each data run must go through.
"""
from database.report.models import WorkflowSummary
from states import StateAction

class WorkflowProcess(object):
    
    def __init__(self, connection=None):
        self._connection = connection
        
    def has_status(self, status):
        """
            Checks that a particular status message type
            exists for this run
        """
        pass
        
    def verify_workflow(self):
        """
            Walk through the data runs and make sure they have
            gone through the whole workflow.
            
            TODO: check whether a message is already in the queue
            The worker nodes might be busy with a previous task.
        """    
        # Get a list of run with an incomplete workflow
        run_list = WorkflowSummary.objects.incomplete()
        for r in run_list:
            r.update()
            if r.complete is False:
                # The workflow for this run is still incomplete
                # Generate a JSON description of the run, to be used
                # when sending a message
                message = r.json_encode()
                
                # Run is not cataloged
                if r.cataloged is False and r.catalog_started is False:
                    StateAction().send(destination='/queue/CATALOG.DATA_READY',
                                       message=message, persistent='true')
            
                # Run hasn't been reduced
                if r.reduction_needed is True and r.reduced is False and \
                    r.reduction_started is False:
                    StateAction().send(destination='/queue/REDUCTION.DATA_READY',
                                       message=message, persistent='true')                    
                
                # Reduced data hasn't been cataloged
                if r.reduction_needed is True and r.reduced is True and \
                    r.reduction_cataloged is False and \
                    r.reduction_catalog_started is False:
                    StateAction().send(destination='/queue/REDUCTION_CATALOG.DATA_READY',
                                       message=message, persistent='true')                    
                    
