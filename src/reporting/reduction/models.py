from django.db import models
from django.contrib.auth.models import User
from report.models import Instrument
  
class ReductionProperty(models.Model):
    """
        Table of template properties for reduction scripts
    """
    instrument = models.ForeignKey(Instrument)
    key        = models.TextField()
    value      = models.TextField(blank=True)
    timestamp  = models.DateTimeField('timestamp', auto_now=True)
    
    class Meta:
        verbose_name_plural = "Reduction properties"

    def __unicode__(self):
        return "%s.%s" % (self.instrument, self.key)

class PropertyModification(models.Model):
    """
        Table of actions taken by users to modify the reduction
        property table.
    """
    property  = models.ForeignKey(ReductionProperty)
    value     = models.TextField(blank=True)
    user      = models.ForeignKey(User)
    timestamp = models.DateTimeField('timestamp', auto_now=True)

class PropertyDefault(models.Model):
    """
        Table of default values
    """
    property  = models.ForeignKey(ReductionProperty, unique=True)
    value     = models.TextField(blank=True)
    timestamp = models.DateTimeField('timestamp', auto_now=True)

class Choice(models.Model):
    """
        Table of choices for forms
    """
    instrument  = models.ForeignKey(Instrument)
    property    = models.ForeignKey(ReductionProperty)
    description = models.TextField()
    value       = models.TextField()

    def __unicode__(self):
        return "%s.%s[%s]" % (self.instrument, self.property, self.description)
