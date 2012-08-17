from django.db import models

class DataRun(models.Model):
    """
        TODO: run number should be unique for a given instrument
        TODO: the instrument name should be part of the run data object
    """
    run_number = models.IntegerField()
    ipts_number = models.IntegerField(null=True)
    instrument = models.CharField(max_length=20, null=True)
    file = models.CharField(max_length=128)
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)

    def __unicode__(self):
        return "%s_%d" % (self.instrument, self.run_number)

    def json_encode(self):
        return {"instrument": self.instrument,
                "ipts": "IPTS-%d" % self.ipts,
                "run_number": self.run_number,
                "data_file": self.file}
    
class StatusQueue(models.Model):
    """
        Table containing the ActiveMQ queue names
        used as status
    """
    name = models.CharField(max_length=100, unique=True)
    
    def __unicode__(self):
        return self.name
    
    
class RunStatusManager(models.Manager):
    
    def status(self, run_id, status_description):
        status_ids = StatusQueue.objects.filter(name__startswith=status_description)
        if len(status_ids)>0:
            status_id = status_ids[0]
            return super(RunStatusManager, self).get_query_set().filter(run_id=run_id, queue_id=status_id)
        return []

class RunStatus(models.Model):
    """
        Map ActiveMQ messages, which have a header like this:
        headers: {'expires': '0', 'timestamp': '1344613053723', 
                  'destination': '/queue/POSTPROCESS.DATA_READY', 
                  'persistent': 'true', 'priority': '5', 
                  'message-id': 'ID:mac83086.ornl.gov-59780-1344536680877-8:2:1:1:1'}
    """
    ## DataRun this run status belongs to
    run_id = models.ForeignKey(DataRun)
    ## Long name for this status
    queue_id = models.ForeignKey(StatusQueue)
    ## ActiveMQ message ID
    message_id = models.CharField(max_length=100, null=True)
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    
    objects = RunStatusManager()
    
    def __unicode__(self):
        return "%s: %s" % (str(self.run_id), str(self.queue_id))
    
    
class WorkflowSummaryManager(models.Manager):
    
    def incomplete(self):
        return super(WorkflowSummaryManager, self).get_query_set().filter(complete=False)
    
        
class WorkflowSummary(models.Model):
    """
        Overall status of the workflow for a given run
    """
    run_id = models.ForeignKey(DataRun)

    # Overall status of the workflow for this run
    complete = models.BooleanField(default=False)
    
    # Cataloging status
    catalog_started = models.BooleanField(default=False)
    cataloged = models.BooleanField(default=False)
    
    # Automated reduction status
    reduction_needed = models.BooleanField(default=True)
    reduction_started = models.BooleanField(default=False)
    reduced = models.BooleanField(default=False)
    reduction_cataloged = models.BooleanField(default=False)
    reduction_catalog_started = models.BooleanField(default=False)
    
    objects = WorkflowSummaryManager()
    
    def update(self):
        """
            Update status according the messages received
        """
        # Look for cataloging status
        if len(RunStatus.objects.status(self.run_id, 'CATALOG.COMPLETE'))>0:
            self.cataloged = True
        if len(RunStatus.objects.status(self.run_id, 'CATALOG.STARTED'))>0:
            self.catalog_started = True
            
        # Check whether we need reduction (default is no)
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION.NOT_NEEDED'))>0:
            self.reduction_needed = False
        
        # Look for reduction status
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION.COMPLETE'))>0:
            self.reduced = True
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION.STARTED'))>0:
            self.reduction_started = True
        
        # Look for status of reduced data cataloging
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION_CATALOG.COMPLETE'))>0:
            self.reduction_cataloged = True
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION_CATALOG.STARTED'))>0:
            self.reduction_catalog_started = True
            
        # Determine overall status
        if self.cataloged is True:
            if self.reduction_needed is False or \
               (self.reduced is True and self.reduction_cataloged is True):
                self.complete = True
                
        self.save()

            
            
            
