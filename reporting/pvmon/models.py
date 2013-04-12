from django.db import models
from report.models import Instrument

class PVName(models.Model):
    name = models.CharField(max_length=50, unique=True)
    monitored = models.BooleanField(default=True)
    
    def __unicode__(self):
        return self.name
    
class PV(models.Model):
    instrument = models.ForeignKey(Instrument, null=True)
    name = models.ForeignKey(PVName)
    value = models.FloatField()
    status = models.IntegerField()
    update_time = models.IntegerField()
    