from reduction.models import ReductionProperty, PropertyModification
from django.contrib import admin
    
class ReductionPropertyAdmin(admin.ModelAdmin):
    list_filter = ('instrument', 'key')
    list_display = ('id', 'instrument', 'key', 'value', 'timestamp')

class PropertyModificationAdmin(admin.ModelAdmin):
    list_filter = ('property', 'user')
    list_display = ('id', 'property', 'value', 'user', 'timestamp')


admin.site.register(ReductionProperty, ReductionPropertyAdmin)
admin.site.register(PropertyModification, PropertyModificationAdmin)


