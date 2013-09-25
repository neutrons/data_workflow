from django.db import models
from report.models import Instrument, DataRun
from django.core.files.storage import FileSystemStorage
from django.conf import settings
  
class ReducedImage(models.Model):
    ## DataRun this run status belongs to
    run_id = models.ForeignKey(DataRun)
    ## Data file
    file = models.FileField(upload_to='images', storage=FileSystemStorage())
    ## Original name
    name = models.CharField(max_length=100)
    created_on = models.DateTimeField('Timestamp', auto_now=True)

    def file_link(self):
        if self.file:
            return "<a href='%s%s'>download</a>" % (settings.MEDIA_URL, self.file.name)
        else:
            return "No attachment"

    file_link.allow_tags = True