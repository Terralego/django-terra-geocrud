from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.postgres import fields
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from . import models, widgets


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

    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }


class CrudLayerAdmin(VersionAdmin):
    list_display = ('pk', 'name', 'geom_type', 'layer_groups')
    list_filter = ('geom_type', 'layer_groups')
    search_fields = ('pk', 'name')
    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }


class CrudFeatureAdmin(VersionAdmin, OSMGeoAdmin):
    list_max_show_all = 50
    list_display = ('pk', 'identifier', 'layer', 'source', 'target')
    list_filter = ('layer', )
    search_fields = ('pk', 'identifier', )
    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }
