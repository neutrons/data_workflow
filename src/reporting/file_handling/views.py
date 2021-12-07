"""
    Handling of reduced data upload

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt

import urllib2
import os
import logging
from report.models import DataRun, Instrument
from file_handling.models import ReducedImage, JsonData
import users.view_util

from django import forms
from django.core.files.base import ContentFile
from django.contrib.auth import login, authenticate


class UploadFileForm(forms.Form):
    """
        Simple form to select a data file on the user's machine
    """
    file = forms.FileField(required=False)
    data_url = forms.URLField(required=False)
    username = forms.CharField()
    password = forms.CharField()


@csrf_exempt
@users.view_util.monitor
def upload_image(request, instrument, run_id):
    """
        Upload an image representing the reduced data
        for a given run
        @param instrument: instrument name
        @param run_id: run number
    """
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            user = authenticate(username=request.POST['username'],
                                password=request.POST['password'])
            if user is not None and not user.is_anonymous():
                login(request, user)
            else:
                return HttpResponse(status=401)
            if not request.user.is_authenticated():
                return HttpResponse(status=401)

            # Prepare to save data to disk
            if 'file' in request.FILES:
                # A file is uploaded directly
                file_name = request.FILES['file'].name
                raw_content = request.FILES['file'].read()
            else:
                # A file URL is provided, fetch it from the URL
                data_url = request.POST['data_url']
                f = urllib2.urlopen(urllib2.Request(url=data_url))
                file_name = data_url
                raw_content = f.read()
            file_content = ContentFile(raw_content)
            # Sanity check
            _, ext = os.path.splitext(file_name)
            if ext.lower() not in ['.jpeg', '.jpg', '.png', '.gif', '.json', '.dat']:
                logging.error("Uploaded file doesn't appear to be an image or json data: %s", file_name)
                return HttpResponse(status=400)
            # Store file info to DB
            # Search to see whether a file with that name exists.
            # Check whether the file is owned by the user before deleting it.
            # If it's not, just create a new file with the same name.
            # Get instrument
            instrument_id = get_object_or_404(Instrument, name=instrument.lower())
            run_object = get_object_or_404(DataRun, instrument_id=instrument_id, run_number=run_id)

            # Look for a data file and treat it differently
            if ext.lower() in ['.json', '.dat']:
                json_data_entries = JsonData.objects.filter(name__endswith=file_name, run_id=run_object)
                if len(json_data_entries) > 0:
                    json_data = json_data_entries[0]
                else:
                    # No entry was found, create one
                    json_data = JsonData()
                    json_data.name = file_name
                    json_data.run_id = run_object
                json_data.data = raw_content
                json_data.save()
            else:
                image_entries = ReducedImage.objects.filter(name__endswith=file_name, run_id=run_object)
                if len(image_entries) > 0:
                    image = image_entries[0]
                    image.file.delete(False)
                else:
                    # No entry was found, create one
                    image = ReducedImage()
                    image.name = file_name
                    image.run_id = run_object
                image.file.save(file_name, file_content)

    else:
        form = UploadFileForm()
        return render(request, 'file_handling/upload.html',
                      {'form': form,
                       'upload_url': reverse('file_handling:upload_image',
                                             args=[instrument, run_id])})
    return HttpResponse()
