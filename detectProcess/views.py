from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse
from .functions import processImage
import os
import base64
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime

# Create your views here.

# homepage
def home(request):
	return render(request, 'index.htm', {'what': 'Slouch Detection'})

# upload api - in this api we handle post requests and send output_image path as a response
def upload(request):
    if request.method == 'POST':
        outputfilepath = handle_uploaded_image(request.POST.get('photoUpload'))
        with open(outputfilepath, "rb") as f:
        	return HttpResponse(outputfilepath)
    return HttpResponse("Failed")

# this function processes the uploaded image
def handle_uploaded_image(photoUploadData):
    # remove out meta info
    photoUploadData = photoUploadData.replace("data:image/jpeg;base64,", "") 

    # if upload folder doesn't exist, we create here
    if not os.path.exists('static/upload/'):
        os.mkdir('static/upload/')
    
    # generate the filename using datetime
    now = datetime.datetime.now()
    filename = now.strftime("%Y%m%d_%H%M%S")
    filepath = 'static/upload/' + filename + '.jpg'

    # save the uploaded image into upload folder
    with open(filepath, 'wb+') as destination:
        destination.write(base64.b64decode(photoUploadData))

    # call image processing function by passing uploaded image file as a parameter
    outputfilepath = processImage(filepath, filename)
    
    return outputfilepath