from django.db import models
from report.models import Instrument

class Parameter(models.Model):
    """
        Table holding the names of the measured quantities
    """
    name = models.CharField(max_length=20, unique=True)
    def __unicode__(self):
        return self.name
    
class ReportedValue(models.Model):
    """
        Table holding the live reported values
    """
    instrument_id = models.ForeignKey(Instrument)
    parameter_id = models.ForeignKey(Parameter)
    value = models.FloatField()
    timestamp = models.DateTimeField('Timestamp')
