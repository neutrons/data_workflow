from file_handling.models import ReducedImage, JsonData
from django.contrib import admin

class ReducedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_id', 'file_link', 'file_size', 'created_on')

class JsonDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_id', 'name', 'created_on')

admin.site.register(ReducedImage, ReducedImageAdmin)
admin.site.register(JsonData, JsonDataAdmin)