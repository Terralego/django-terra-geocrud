from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.postgres import fields
from django.utils.translation import gettext_lazy as _
from geostore.models import LayerExtraGeom
from reversion.admin import VersionAdmin
from sorl.thumbnail.admin import AdminInlineImageMixin

from . import models, widgets


class CrudGroupViewAdmin(VersionAdmin):
    list_display = ['name', 'order', 'pictogram']


class FeatureDisplayGroupTabularInline(admin.TabularInline):
    classes = ('collapse', )
    verbose_name = _('Display group')
    verbose_name_plural = _('Display groups for feature property display and form.')
    model = models.FeaturePropertyDisplayGroup
    extra = 0


class ExtraLayerStyleInLine(admin.TabularInline):
    model = models.ExtraLayerStyle
    extra = 0


class CrudViewAdmin(VersionAdmin):
    list_display = ['name', 'order', 'pictogram', 'properties', ]
    list_filter = ['group', ]
    inlines = [FeatureDisplayGroupTabularInline, ExtraLayerStyleInLine]
    readonly_fields = ['grouped_form_schema', 'properties']
    fieldsets = (
        (None, {'fields': (('name', 'object_name', 'object_name_plural', 'layer'), ('group', 'order', 'pictogram'))}),
        (_('UI schema & properties'), {
            'fields': ('properties', 'default_list_properties', 'feature_title_property', 'ui_schema'),
            'classes': ('collapse', )
        }),
        (_("Document generation"), {
            'fields': ('templates',),
            'classes': ('collapse', )
        }),
        (_("Other settings"), {
            'fields': (('map_style', 'settings'),),
            'classes': ('collapse', )
        }),
    )

    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }

    def get_readonly_fields(self, request, obj=None):
        ro_fields = list(super().get_readonly_fields(request, obj=obj))
        if obj and obj.pk:
            # dont change layer after creation
            ro_fields += ('layer', )
        return ro_fields


class LayerExtraGeomInline(admin.TabularInline):
    model = LayerExtraGeom
    extra = 0


class CrudLayerAdmin(VersionAdmin):
    list_display = ('pk', 'name', 'geom_type', 'layer_groups')
    list_filter = ('geom_type', 'layer_groups')
    search_fields = ('pk', 'name')
    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }
    inlines = [LayerExtraGeomInline, ]


class FeaturePictureInline(AdminInlineImageMixin, admin.TabularInline):
    classes = ('collapse', )
    verbose_name = _('Picture')
    verbose_name_plural = _('Pictures')
    model = models.FeaturePicture
    extra = 0


class FeatureAttachmentInline(admin.TabularInline):
    classes = ('collapse', )
    verbose_name = _('Attachment')
    verbose_name_plural = _('Attachments')
    model = models.FeatureAttachment
    extra = 0


class CrudFeatureAdmin(VersionAdmin, OSMGeoAdmin):
    list_max_show_all = 50
    list_display = ('pk', 'identifier', 'layer', 'source', 'target')
    list_filter = ('layer', )
    search_fields = ('pk', 'identifier', )
    inlines = (FeaturePictureInline, FeatureAttachmentInline)
    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }


class AttachmentCategoryAdmin(VersionAdmin):
    list_display = ('pk', 'name', 'pictogram')
    search_fields = ('pk', 'name', )
