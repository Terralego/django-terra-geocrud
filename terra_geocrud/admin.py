from django.contrib import admin
from django.contrib.postgres import fields

from geostore.admin import LayerAdmin
from geostore.models import Layer
from . import models
from .jsoneditor import JSONEditorWidget


@admin.register(models.CrudGroupView)
class CrudGroupViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram']


class FeatureDisplayGroupTabularInline(admin.TabularInline):
    model = models.FeaturePropertyDisplayGroup
    extra = 0


class PropertyDisplayRenderingTabularInline(admin.TabularInline):
    model = models.PropertyDisplayRendering
    extra = 0


@admin.register(models.CrudView)
class CrudViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram', 'properties', ]
    list_filter = ['group', ]
    inlines = [FeatureDisplayGroupTabularInline, PropertyDisplayRenderingTabularInline]
    readonly_fields = ['form_schema', 'properties']
    fieldsets = (
        (None, {'fields': (('name', 'layer'), ('group', 'order', 'pictogram'))}),
        ('Feature properties', {'fields': ('properties', 'default_list_properties', 'feature_title_property')}),
        ("Document generation", {'fields': ('templates', )}),
        ("Schema", {'fields': ('ui_schema', )}),
        ("Other settings", {'fields': (('map_style', 'settings'), )}),
    )

    def get_readonly_fields(self, request, obj=None):
        ro_fields = super().get_readonly_fields(request, obj=obj)
        if obj and obj.pk:
            ro_fields += ['layer']

        return ro_fields

    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }


admin.site.unregister(Layer)
@admin.register(Layer)
class CrudLayerAdmin(LayerAdmin):
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }
