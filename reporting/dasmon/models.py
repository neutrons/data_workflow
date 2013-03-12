from django.db import models
from report.models import Instrument
    
class Parameter(models.Model):
    """
        Table holding the names of the measured quantities
    """
    name = models.CharField(max_length=128, unique=True)
    monitored = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name
    
class StatusVariable(models.Model):
    """
        Table containing key-value pairs from the DASMON
    """
    instrument_id = models.ForeignKey(Instrument)
    key_id   = models.ForeignKey(Parameter)
    value = models.CharField(max_length=128)
    timestamp = models.DateTimeField('timestamp', auto_now_add=True)