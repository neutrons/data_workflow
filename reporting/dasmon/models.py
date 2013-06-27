from django.db import models
from report.models import Instrument
    
class Parameter(models.Model):
    """
        Table holding the names of the measured quantities
    """
    name      = models.CharField(max_length=128, unique=True)
    monitored = models.BooleanField(default=True)
    
    def __unicode__(self):
        return self.name
    
class StatusVariable(models.Model):
    """
        Table containing key-value pairs from the DASMON
    """
    instrument_id = models.ForeignKey(Instrument)
    key_id        = models.ForeignKey(Parameter)
    value         = models.CharField(max_length=128)
    timestamp     = models.DateTimeField('timestamp', auto_now_add=True)
    
class StatusCache(models.Model):
    instrument_id = models.ForeignKey(Instrument)
    key_id        = models.ForeignKey(Parameter)
    value         = models.CharField(max_length=128)
    timestamp     = models.DateTimeField('timestamp')

class ActiveInstrumentManager(models.Manager):
    
    def is_alive(self, instrument_id):
        instrument_list = super(ActiveInstrumentManager, self).get_query_set().filter(instrument_id=instrument_id)
        if len(instrument_list)>0:
            return instrument_list[0].is_alive
        else:
            return True
    
class ActiveInstrument(models.Model):
    """
        Table containing the list of instruments that are expecting to
        have their DAS turned ON
    """
    instrument_id = models.ForeignKey(Instrument, unique=True)
    is_alive = models.BooleanField(default=True)
    objects = ActiveInstrumentManager()