"""
Dasmon app models
@author: M. Doucet, Oak Ridge National Laboratory
@copyright: 2015 Oak Ridge National Laboratory
"""

from django.db import models
from reporting.report.models import Instrument


class Parameter(models.Model):
    """
    Table holding the names of the measured quantities
    """

    name = models.CharField(max_length=128, unique=True)
    monitored = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StatusVariable(models.Model):
    """
    Table containing key-value pairs from the DASMON
    """

    id = models.BigAutoField(primary_key=True)
    instrument_id = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    key_id = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=128)
    timestamp = models.DateTimeField("timestamp", auto_now_add=True)


class StatusCache(models.Model):
    """
    Table of cached status variable values
    """

    instrument_id = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    key_id = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=128)
    timestamp = models.DateTimeField("timestamp", auto_now=True)


class ActiveInstrumentManager(models.Manager):
    """
    Table of options for instruments
    """

    def is_alive(self, instrument_id):
        """
        Returns True if the instrument should be presented as part of the suite of instruments
        """
        instrument_list = super(ActiveInstrumentManager, self).get_queryset().filter(instrument_id=instrument_id)
        if len(instrument_list) > 0:
            return instrument_list[0].is_alive
        else:
            return True

    def is_adara(self, instrument_id):
        """
        Returns True if the instrument is running ADARA
        """
        instrument_list = super(ActiveInstrumentManager, self).get_queryset().filter(instrument_id=instrument_id)
        if len(instrument_list) > 0:
            return instrument_list[0].is_adara
        else:
            return True

    def has_pvsd(self, instrument_id):
        """
        Returns True if the instrument is running pvsd
        Defaults to False
        """
        instrument_list = super(ActiveInstrumentManager, self).get_queryset().filter(instrument_id=instrument_id)
        if len(instrument_list) > 0:
            return instrument_list[0].has_pvsd
        else:
            return False

    def has_pvstreamer(self, instrument_id):
        """
        Returns True if the instrument is running PVStreamer
        Defaults to True
        """
        instrument_list = super(ActiveInstrumentManager, self).get_queryset().filter(instrument_id=instrument_id)
        if len(instrument_list) > 0:
            return instrument_list[0].has_pvstreamer
        else:
            return True


class ActiveInstrument(models.Model):
    """
    Table containing the list of instruments that are expecting to
    have their DAS turned ON
    """

    instrument_id = models.OneToOneField(Instrument, on_delete=models.CASCADE)
    is_alive = models.BooleanField(default=True)
    is_adara = models.BooleanField(default=True)
    has_pvsd = models.BooleanField(default=False)
    has_pvstreamer = models.BooleanField(default=True)
    objects = ActiveInstrumentManager()


class Signal(models.Model):
    """
    Table of signals received from DASMON
    """

    instrument_id = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    source = models.CharField(max_length=40)
    message = models.CharField(max_length=250)
    level = models.IntegerField()
    timestamp = models.DateTimeField("timestamp")


class UserNotification(models.Model):
    """
    Table of users to notify
    """

    user_id = models.IntegerField(unique=True)
    instruments = models.ManyToManyField(Instrument, related_name="_usernotification_instruments+")
    email = models.EmailField(max_length=254)
    registered = models.BooleanField(default=False)
