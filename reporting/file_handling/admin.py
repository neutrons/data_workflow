from file_handling.models import ReducedImage
from django.contrib import admin

class ReducedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_id', 'file_link', 'file_size', 'created_on')

admin.site.register(ReducedImage, ReducedImageAdmin)