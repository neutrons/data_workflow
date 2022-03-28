from django.db import models
from django.contrib.auth.models import User
from reporting.report.models import Instrument


class ReductionProperty(models.Model):
    """
    Table of template properties for reduction scripts
    """

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    key = models.TextField()
    value = models.TextField(blank=True)
    timestamp = models.DateTimeField("timestamp", auto_now=True)

    class Meta:
        verbose_name_plural = "Reduction properties"

    def __str__(self):
        return "%s.%s" % (self.instrument, self.key)


class PropertyModification(models.Model):
    """
    Table of actions taken by users to modify the reduction
    property table.
    """

    property = models.ForeignKey(ReductionProperty, on_delete=models.CASCADE)
    value = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField("timestamp", auto_now=True)


class PropertyDefault(models.Model):
    """
    Table of default values
    """

    property = models.ForeignKey(ReductionProperty, unique=True, on_delete=models.CASCADE)
    value = models.TextField(blank=True)
    timestamp = models.DateTimeField("timestamp", auto_now=True)


class Choice(models.Model):
    """
    Table of choices for forms
    """

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    property = models.ForeignKey(ReductionProperty, on_delete=models.CASCADE)
    description = models.TextField()
    value = models.TextField()

    def __str__(self):
        return "%s.%s[%s]" % (self.instrument, self.property, self.description)
