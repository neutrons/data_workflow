from django.db import models

class PVName(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
class PV(models.Model):
    name = models.ForeignKey(PVName)
    value = models.FloatField()
    status = models.IntegerField()
    update_time = models.IntegerField()
    