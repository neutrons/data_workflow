from reduction.models import (
    ReductionProperty,
    PropertyModification,
    Choice,
    PropertyDefault,
)
from django.contrib import admin


class ReductionPropertyAdmin(admin.ModelAdmin):
    list_filter = ("instrument", "key")
    list_display = ("id", "instrument", "key", "value", "timestamp")


class PropertyModificationAdmin(admin.ModelAdmin):
    list_filter = ("property", "user")
    list_display = ("id", "property", "value", "user", "timestamp")


class PropertyDefaultAdmin(admin.ModelAdmin):
    list_display = ("id", "property", "value", "timestamp")


class ChoiceAdmin(admin.ModelAdmin):
    list_filter = ("instrument",)
    list_display = ("id", "instrument", "property", "description", "value")


admin.site.register(ReductionProperty, ReductionPropertyAdmin)
admin.site.register(PropertyModification, PropertyModificationAdmin)
admin.site.register(PropertyDefault, PropertyDefaultAdmin)
admin.site.register(Choice, ChoiceAdmin)
