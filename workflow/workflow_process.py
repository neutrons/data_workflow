"""
    Actual process that each data run must go through.
"""
from database.report.models import WorkflowSummary, RunStatus
from django.utils.timezone import utc
from states import StateAction
import json
import logging
import datetime

class WorkflowProcess(object):
    
    def __init__(self, connection=None, recovery=False, allowed_lag=None):
        """
            @param recovery: if True, the system will try to recover from workflow problems
            @param allowed_lag: minimum number of seconds since last activity needed before identifying a problem
        """
        self._connection = connection
        self._recovery = recovery
        # Amount of time allowed before we start worrying about workflow issues
        if allowed_lag is None:
            self._allowed_lag = datetime.timedelta(days=1)
        else:
            self._allowed_lag = datetime.timedelta(seconds=allowed_lag)
        
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
        """    
        logging.info("Verifying workflow completeness")
        # Get a list of run with an incomplete workflow
        run_list = WorkflowSummary.objects.incomplete()
        logging.info(" - list generated")
        
        for r in run_list:            
            r.update()
            # Identify a problem only if the last message received is more
            # than a minimum amount of time
            now = datetime.datetime.utcnow().replace(tzinfo=utc)
            if r.complete is False and \
                now-RunStatus.objects.last_timestamp(r.run_id)>self._allowed_lag:
                # The workflow for this run is still incomplete
                # Generate a JSON description of the run, to be used
                # when sending a message
                message = r.run_id.json_encode()
                data_dict = json.loads(message)
                
                # Run is not cataloged
                if r.cataloged is False:
                    data_dict["information"] = "Cataloging incomplete for %s" % str(r)
                    logging.warn(data_dict["information"])
                    message = json.dumps(data_dict)
                    StateAction().send(destination='/queue/POSTPROCESS.INFO',
                                       message=message, persistent='true')
                    if self._recovery:
                        StateAction().send(destination='/queue/CATALOG.DATA_READY',
                                           message=message, persistent='true')
            
                # Run hasn't been reduced
                if r.reduction_needed is True and r.reduced is False:
                    data_dict["information"] = "Reduction incomplete for %s" % str(r)
                    logging.warn(data_dict["information"])
                    message = json.dumps(data_dict)
                    StateAction().send(destination='/queue/POSTPROCESS.INFO',
                                       message=message, persistent='true')
                    if self._recovery:
                        StateAction().send(destination='/queue/REDUCTION.DATA_READY',
                                           message=message, persistent='true')                    
                
                # Reduced data hasn't been cataloged
                if r.reduction_needed is True and r.reduced is True and \
                    r.reduction_cataloged is False:
                    data_dict["information"] = "Reduction cataloging incomplete for %s" % str(r)
                    logging.warn(data_dict["information"])
                    message = json.dumps(data_dict)
                    StateAction().send(destination='/queue/POSTPROCESS.INFO',
                                       message=message, persistent='true')
                    if self._recovery:
                        StateAction().send(destination='/queue/REDUCTION_CATALOG.DATA_READY',
                                           message=message, persistent='true')                    
        logging.info(" - verification completed")
