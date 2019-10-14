from django.contrib import admin
from django.contrib.postgres import fields
from django.utils.translation import gettext_lazy as _

from geostore.admin import LayerAdmin, FeatureAdmin
from geostore.models import Layer, Feature
from reversion.admin import VersionAdmin

from . import models
from .jsoneditor import JSONEditorWidget

admin.site.unregister(Layer)
admin.site.unregister(Feature)


@admin.register(models.CrudGroupView)
class CrudGroupViewAdmin(VersionAdmin):
    list_display = ['name', 'order', 'pictogram']


class FeatureDisplayGroupTabularInline(admin.TabularInline):
    verbose_name = _('Display group')
    verbose_name_plural = _('Display groups for feature property display and form.')
    model = models.FeaturePropertyDisplayGroup
    extra = 0


class PropertyDisplayRenderingTabularInline(admin.TabularInline):
    verbose_name = _('Custom widget')
    verbose_name_plural = _('Custom widgets for property content display rendering')
    model = models.PropertyDisplayRendering
    extra = 0


@admin.register(models.CrudView)
class CrudViewAdmin(VersionAdmin):
    list_display = ['name', 'order', 'pictogram', 'properties', ]
    list_filter = ['group', ]
    inlines = [FeatureDisplayGroupTabularInline, PropertyDisplayRenderingTabularInline]
    readonly_fields = ['grouped_form_schema', 'properties']
    fieldsets = (
        (None, {'fields': (('name', 'layer'), ('group', 'order', 'pictogram'))}),
        ('Feature properties', {'fields': ('properties', 'default_list_properties', 'feature_title_property')}),
        ("Document generation", {'fields': ('templates',)}),
        ("Schema", {'fields': ('ui_schema',)}),
        ("Other settings", {'fields': (('map_style', 'settings'),)}),
    )

    def get_readonly_fields(self, request, obj=None):
        ro_fields = super().get_readonly_fields(request, obj=obj)
        if obj and obj.pk:
            ro_fields += ['layer']

        return ro_fields

    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }


@admin.register(Layer)
class CrudLayerAdmin(VersionAdmin, LayerAdmin):
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }


@admin.register(Feature)
class CrudFeatureAdmin(VersionAdmin, FeatureAdmin):
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }
