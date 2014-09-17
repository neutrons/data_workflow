from django.db import models
from django.contrib.auth.models import User
from report.models import Instrument
  
class ReductionProperty(models.Model):
    """
        Table of template properties for reduction scripts
    """
    instrument = models.ForeignKey(Instrument)
    key        = models.TextField()
    value      = models.TextField()
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
    value     = models.TextField()
    user      = models.ForeignKey(User)
    timestamp = models.DateTimeField('timestamp', auto_now=True)

