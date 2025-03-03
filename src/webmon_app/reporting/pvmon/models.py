"""
Models for PV monitor app

@author: M. Doucet, Oak Ridge National Laboratory
@copyright: 2014 Oak Ridge National Laboratory
"""

from django.db import models

from reporting.report.models import Instrument


class PVName(models.Model):
    """
    Table holding the Process Variable names
    """

    name = models.CharField(max_length=50, unique=True)
    monitored = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PV(models.Model):
    """
    Table holding values
    """

    id = models.BigAutoField(primary_key=True)
    instrument = models.ForeignKey(Instrument, null=True, on_delete=models.CASCADE)
    name = models.ForeignKey(PVName, on_delete=models.CASCADE)
    value = models.FloatField()
    status = models.IntegerField()
    update_time = models.IntegerField()

    class Meta:
        verbose_name_plural = "PVs"


class PVCache(models.Model):
    """
    Table holding the latest values
    """

    instrument = models.ForeignKey(Instrument, null=True, on_delete=models.CASCADE)
    name = models.ForeignKey(PVName, on_delete=models.CASCADE)
    value = models.FloatField()
    status = models.IntegerField()
    update_time = models.IntegerField()

    class Meta:
        verbose_name_plural = "PV cache"


class PVString(models.Model):
    """
    Table holding string values
    """

    instrument = models.ForeignKey(Instrument, null=True, on_delete=models.CASCADE)
    name = models.ForeignKey(PVName, on_delete=models.CASCADE)
    value = models.TextField()
    status = models.IntegerField()
    update_time = models.IntegerField()

    class Meta:
        verbose_name_plural = "PV strings"


class PVStringCache(models.Model):
    """
    Table holding the latest string values
    """

    instrument = models.ForeignKey(Instrument, null=True, on_delete=models.CASCADE)
    name = models.ForeignKey(PVName, on_delete=models.CASCADE)
    value = models.TextField()
    status = models.IntegerField()
    update_time = models.IntegerField()

    class Meta:
        verbose_name_plural = "PV string cache"


class MonitoredVariable(models.Model):
    """
    Table of PVs that need special monitoring
    and might have DASMON rules associated with them
    """

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    pv_name = models.ForeignKey(PVName, null=True, blank=True, on_delete=models.CASCADE)
    rule_name = models.CharField(max_length=50, default="", blank=True)
