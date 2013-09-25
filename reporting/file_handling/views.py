from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

import urllib2
from report.models import DataRun, Instrument
from file_handling.models import ReducedImage
import users.view_util

from django import forms
from django.core.files.base import ContentFile


class UploadFileForm(forms.Form):
    """
        Simple form to select a data file on the user's machine
    """
    # http://dl.dropbox.com/u/16900303/5731_frame1_Iq.xml
    file  = forms.FileField(required=False)
    data_url = forms.URLField(required=False, verify_exists=True)


@users.view_util.login_or_local_required
@users.view_util.monitor
def upload_image(request, instrument, run_id):
    """
        Upload an image representing the reduced data 
        for a given run
        @param instrument: instrument name
        @param run_id: run number
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    run_object = get_object_or_404(DataRun, instrument_id=instrument_id,run_number=run_id)

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Prepare to save data to disk
            if 'file' in request.FILES:
                # A file is uploaded directly
                file_name = request.FILES['file'].name
                file_content = ContentFile(request.FILES['file'].read())
            else:
                # A file URL is provided, fetch it from the URL
                data_url = request.POST['data_url']
                f = urllib2.urlopen(urllib2.Request(url=data_url))
                file_name = data_url
                file_content = ContentFile(f.read())
            # Store file info to DB
            # Search to see whether a file with that name exists.
            # Check whether the file is owned by the user before deleting it.
            # If it's not, just create a new file with the same name.
            image_entries = ReducedImage.objects.filter(name__endswith=file_name, run_id=run_object)
            if len(image_entries)>0:                
                image = image_entries[0]
                image.file.delete(False)
            else:
                # No entry was found, create one
                image = ReducedImage()
                image.name  = file_name
                image.run_id = run_object
            
            image.file.save(file_name, file_content)
            
    else:
        form = UploadFileForm()
        return render_to_response('file_handling/upload.html', 
                                  {'form': form,
                                   'upload_url': reverse('file_handling.views.upload_image',
                                                         args=[instrument, run_id])},
                                  context_instance=RequestContext(request))
    return HttpResponse()


