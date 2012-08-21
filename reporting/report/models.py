from django.db import models

class InstrumentManager(models.Manager):
    def find_instrument(self, instrument):
        """
            Get the object associated to an instrument name
        """
        instrument_ids = super(InstrumentManager, self).get_query_set().filter(name=instrument.lower())
        if len(instrument_ids) > 0:
            return instrument_ids[0]
        return None
        

class Instrument(models.Model):
    name = models.CharField(max_length=20, unique=True)
    objects = InstrumentManager()
    def __unicode__(self):
        return self.name
    
    def number_of_runs(self):
        return DataRun.objects.filter(instrument_id=self).count()
    
    
class IPTSManager(models.Manager):
    
    def ipts_for_instrument(self, instrument_id):
        return super(IPTSManager, self).get_query_set().filter(instrument_id=instrument_id)
        
        
class IPTS(models.Model):
    """
        Table holding IPTS information
    """
    expt_name = models.CharField(max_length=20, unique=True)
    instruments = models.ManyToManyField(Instrument)
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    objects = IPTSManager()
    
    def __unicode__(self):
        return self.expt_name
    
    def number_of_runs(self, instrument_id=None):
        if instrument_id is None:
            return DataRun.objects.filter(ipts_id=self).distinct().count()
        return DataRun.objects.filter(ipts_id=self, instrument_id=instrument_id)

    
class DataRun(models.Model):
    """
        TODO: run number should be unique for a given instrument
        TODO: the instrument name should be part of the run data object
    """
    run_number = models.IntegerField()
    ipts_id = models.ForeignKey(IPTS)
    instrument_id = models.ForeignKey(Instrument)
    file = models.CharField(max_length=128)
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)

    def __unicode__(self):
        return "%s_%d" % (self.instrument_id, self.run_number)

    def json_encode(self):
        """
            Encode the object as a JSON dictionnary
        """
        return {"instrument": self.instrument_id,
                "ipts": str(self.ipts_id),
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
        """
            Returns all database entries for a given run and a given
            status message.
            @param run_id: DataRun object
            @param status_description: status message, as a string
        """
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
        """
            Returns the query set of all incomplete runs
        """
        return super(WorkflowSummaryManager, self).get_query_set().filter(complete=False)
    
    def get_summary(self, run_id):
        """
            Get the run summary for a given DataRun object
            @param run_id: DataRun object
        """
        run_list = super(WorkflowSummaryManager, self).get_query_set().filter(run_id=run_id)
        if len(run_list)>0:
            return run_list[0]
        return None
        
class WorkflowSummary(models.Model):
    """
        Overall status of the workflow for a given run
    """
    run_id = models.ForeignKey(DataRun, unique=True)

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
    
    def __unicode__(self):
        if self.complete is True:
            return "%s: complete" % str(self.run_id)
        else:
            return str(self.run_id)
    
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

         
class Errors(models.Model):
    """
        Details of a particular error event
    """   
    run_status_id = models.ForeignKey(RunStatus)
    description = models.CharField(max_length=200, null=True)
            
