from django.db import models

class DataRun(models.Model):
    """
    TODO: run number should be unique for a given instrument
    TODO: the instrument name should be part of the run data object
    """
    run_number = models.IntegerField()
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    
class StatusInfo(models.Model):
    """
        Table containing the ActiveMQ destination names
        used as status
    """
    name = models.CharField(max_length=100)
    
class RunStatus(models.Model):
    """
        Map ActiveMQ messages, which have a header like this:
        headers: {'expires': '0', 'timestamp': '1344613053723', '
                  destination': '/queue/POSTPROCESS.DATA_READY', 
                  'persistent': 'true', 'priority': '5', 
                  'message-id': 'ID:mac83086.ornl.gov-59780-1344536680877-8:2:1:1:1'}
    """
    ## DataRun this run status belongs to
    run_id = models.ForeignKey(DataRun)
    ## Long name for this status
    queue_id = models.ForeignKey(StatusInfo)
    ## ActiveMQ message ID
    message_id = models.CharField(max_length=100, null=True)
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    
