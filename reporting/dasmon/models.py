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
        """
            Returns True if the instrument should be presented as part of the suite of instruments
        """
        instrument_list = super(ActiveInstrumentManager, self).get_queryset().filter(instrument_id=instrument_id)
        if len(instrument_list)>0:
            return instrument_list[0].is_alive
        else:
            return True
    
    def is_adara(self, instrument_id):
        """
            Returns True if the instrument is running ADARA
        """
        instrument_list = super(ActiveInstrumentManager, self).get_queryset().filter(instrument_id=instrument_id)
        if len(instrument_list)>0:
            return instrument_list[0].is_adara
        else:
            return True

    def has_pvsd(self, instrument_id):
        """
            Returns True if the instrument is running pvsd
            Defaults to False
        """
        instrument_list = super(ActiveInstrumentManager, self).get_queryset().filter(instrument_id=instrument_id)
        if len(instrument_list)>0:
            return instrument_list[0].has_pvsd
        else:
            return False

    def has_pvstreamer(self, instrument_id):
        """
            Returns True if the instrument is running PVStreamer
            Defaults to True
        """
        instrument_list = super(ActiveInstrumentManager, self).get_queryset().filter(instrument_id=instrument_id)
        if len(instrument_list)>0:
            return instrument_list[0].has_pvstreamer
        else:
            return True


class ActiveInstrument(models.Model):
    """
        Table containing the list of instruments that are expecting to
        have their DAS turned ON
    """
    instrument_id = models.ForeignKey(Instrument, unique=True)
    is_alive      = models.BooleanField(default=True)
    is_adara      = models.BooleanField(default=True)
    has_pvsd      = models.BooleanField(default=False)
    has_pvstreamer= models.BooleanField(default=True)
    objects       = ActiveInstrumentManager()
    
    
class Signal(models.Model):
    """
        Table of signals received from DASMON
    """
    instrument_id = models.ForeignKey(Instrument)
    name          = models.CharField(max_length=128)
    source        = models.CharField(max_length=40)
    message       = models.CharField(max_length=250)
    level         = models.IntegerField()
    timestamp     = models.DateTimeField('timestamp')
    
class LegacyURL(models.Model):
    """
        Table of URLs pointing to the legacy instrument status service
    """
    instrument_id = models.ForeignKey(Instrument, unique=True)
    url = models.CharField(max_length=128)
    long_name = models.CharField(max_length=40)
    
    