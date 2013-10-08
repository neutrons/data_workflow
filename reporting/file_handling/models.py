from django.db import models
from report.models import Instrument, DataRun
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.dispatch import receiver
import os
  
class ReducedImage(models.Model):
    """
        Table of image files corresponding to plots of reduced
        data for a given run.
    """
    ## DataRun this run status belongs to
    run_id = models.ForeignKey(DataRun)
    ## Data file
    file = models.FileField(upload_to='images', storage=FileSystemStorage())
    ## Original name
    name = models.CharField(max_length=100)
    created_on = models.DateTimeField('Timestamp', auto_now=True)

    def file_link(self):
        if self.file:
            return "<a href='%s%s'>%s</a>" % (settings.MEDIA_URL, self.file.name, self.name)
        else:
            return "No attachment"

    file_link.allow_tags = True
    
    def file_size(self):
        if self.file:
            return str(self.file.size)
        else:
            return "N/A"
    file_size.short_description = "Bytes"
    
# These two auto-delete files from filesystem when they are unneeded:
@receiver(models.signals.post_delete, sender=ReducedImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
        Deletes file from filesystem
        when corresponding ReducedImage object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)

@receiver(models.signals.pre_save, sender=ReducedImage)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
        Deletes file from filesystem
        when corresponding ReducedImage object is changed.
    """
    if not instance.pk:
        return False

    try:
        old_file = ReducedImage.objects.get(pk=instance.pk).file
    except ReducedImage.DoesNotExist:
        return False

    new_file = instance.file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
