from django.db import models
from django.contrib.auth.models import User

class TruncatingCharField(models.CharField):
    def get_prep_value(self, value):
        value = super(TruncatingCharField,self).get_prep_value(value)
        if value:
            return value[:self.max_length]
        return value
    
class PageView(models.Model):
    user = models.ForeignKey(User, null=True)
    view = TruncatingCharField(max_length=64)
    path = TruncatingCharField(max_length=128)
    ip = models.CharField(max_length=64)
    timestamp = models.DateTimeField('timestamp', auto_now_add=True)

class DeveloperNode(models.Model):
    """
        Table of IP names recognized as developer nodes
    """
    ip = models.CharField(max_length=64)