from django.db import models
from report.models import Instrument

class PVName(models.Model):
    """
        Table holding the Process Variable names
    """
    name = models.CharField(max_length=50, unique=True)
    monitored = models.BooleanField(default=True)
    
    def __unicode__(self):
        return self.name
    

class PV(models.Model):
    """
        Table holding values
    """
    instrument = models.ForeignKey(Instrument, null=True)
    name = models.ForeignKey(PVName)
    value = models.FloatField()
    status = models.IntegerField()
    update_time = models.IntegerField()
    

class PVCache(models.Model):
    """
        Table holding the latest values
    """
    instrument = models.ForeignKey(Instrument, null=True)
    name = models.ForeignKey(PVName)
    value = models.FloatField()
    status = models.IntegerField()
    update_time = models.IntegerField()
    

class MonitoredVariable(models.Model):
    """
        Table of PVs that need special monitoring
        and might have DASMON rules associated with them
    """
    instrument = models.ForeignKey(Instrument)
    pv_name = models.ForeignKey(PVName, null=True, blank=True)
    rule_name = models.CharField(max_length=50, default='', blank=True)
    