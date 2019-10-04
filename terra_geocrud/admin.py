from django.contrib import admin
from django.contrib.postgres.fields import JSONField
from geostore.admin import LayerAdmin, FeatureAdmin

from geostore.models import Layer, Feature

from jsoneditor.forms import JSONEditor


from . import models


@admin.register(models.CrudGroupView)
class CrudGroupViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram']


class FeatureDisplayGroupTabularInline(admin.TabularInline):
    model = models.FeaturePropertyDisplayGroup
    extra = 0


@admin.register(models.CrudView)
class CrudViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram', 'properties', ]
    list_filter = ['group', ]
    inlines = [FeatureDisplayGroupTabularInline, ]
    readonly_fields = ['form_schema', 'properties']
    fieldsets = (
        (None, {'fields': (('name', 'layer'), ('group', 'order', 'pictogram'))}),
        ('Feature list', {'fields': ('properties', 'default_list_properties')}),
        ("Document generation", {'fields': ('templates', )}),
        ("Schema", {'fields': ('ui_schema', )}),
        ("Other settings", {'fields': (('map_style', 'settings'), )}),
    )

    def get_readonly_fields(self, request, obj=None):
        ro_fields = super().get_readonly_fields(request, obj=obj)
        if obj and obj.pk:
            return ro_fields + ['layer']

        return ro_fields

    formfield_overrides = {
        JSONField: {'widget': JSONEditor},
    }


admin.site.unregister(Layer)


@admin.register(Layer)
class CrudLayerModelAdmin(LayerAdmin):
    formfield_overrides = {
        JSONField: {'widget': JSONEditor},
    }


admin.site.unregister(Feature)


@admin.register(Feature)
class CrudFeatureModelAdmin(FeatureAdmin):
    formfield_overrides = {
        JSONField: {'widget': JSONEditor},
    }
