from admin_ordering.admin import OrderableAdmin
from django.contrib import admin, messages
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.postgres import fields
from django.utils.translation import gettext_lazy as _
from django_json_widget.widgets import JSONEditorWidget
from django_object_actions import DjangoObjectActions
from geostore.models import LayerExtraGeom, FeatureExtraGeom
from reversion.admin import VersionAdmin
from sorl.thumbnail.admin import AdminInlineImageMixin

from . import models, forms
from .properties.schema import sync_layer_schema, sync_ui_schema, clean_properties_not_in_schema_or_null


class CrudGroupViewAdmin(OrderableAdmin, VersionAdmin):
    ordering_field = "order"
    list_editable = ["order"]
    list_display = ['name', 'order', 'pictogram']


class FeatureDisplayGroupTabularInline(OrderableAdmin, admin.TabularInline):
    ordering_field = "order"
    classes = ('collapse', )
    verbose_name = _('Display group')
    verbose_name_plural = _('Display groups for feature property display and form.')
    model = models.FeaturePropertyDisplayGroup
    extra = 0


class ExtraLayerStyleInLine(admin.TabularInline):
    classes = ('collapse', )
    verbose_name = _('Extra layer style')
    verbose_name_plural = _('Extra layer styles')
    model = models.ExtraLayerStyle
    form = forms.ExtraLayerStyleForm
    extra = 0
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }


class CrudPropertyInline(OrderableAdmin, admin.TabularInline):
    ordering_field = "order"
    classes = ('collapse', )
    verbose_name = _("Feature property")
    verbose_name_plural = _("Feature properties")
    model = models.CrudViewProperty
    form = forms.CrudPropertyForm
    extra = 0
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget(height=200)},
    }


class CrudViewAdmin(OrderableAdmin, DjangoObjectActions, VersionAdmin):
    ordering_field = "order"
    list_editable = ["order"]
    filter_horizontal = ('default_list_properties', )
    form = forms.CrudViewForm
    list_display = ['name', 'group', 'order', 'pictogram']
    list_filter = ['group', ]
    inlines = [CrudPropertyInline, FeatureDisplayGroupTabularInline, ExtraLayerStyleInLine]
    readonly_fields = ['ui_schema']
    fieldsets = (
        (None, {'fields': (('name', 'object_name', 'object_name_plural', 'layer'), ('group', 'order', 'pictogram'))}),
        (_('UI schema & properties'), {
            'fields': ('default_list_properties', 'feature_title_property', 'ui_schema'),
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
        fields.JSONField: {'widget': JSONEditorWidget},
    }

    def get_readonly_fields(self, request, obj=None):
        ro_fields = list(super().get_readonly_fields(request, obj=obj))
        if obj and obj.pk:
            # dont change layer after creation
            ro_fields += ('layer', )
        return ro_fields

    def sync_schemas(self, request, obj):
        sync_layer_schema(obj)
        sync_ui_schema(obj)
        messages.success(request,
                         _("Layer json schema and crud view ui schema have been synced with crud view properties."))

    sync_schemas.label = _("Sync schemas")
    sync_schemas.short_description = _("Sync layer schema and crud view ui schema with defined properties.")

    def clean_feature_properties(self, request, obj):
        clean_properties_not_in_schema_or_null(obj)
        messages.success(request, _("Feature properties has been cleaned."))

    clean_feature_properties.label = _("Clean features with schema")
    clean_feature_properties.short_description = _("Clean feature properties not in generated layer schema.")

    change_actions = ('sync_schemas', 'clean_feature_properties')


class LayerExtraGeomInline(admin.TabularInline):
    model = LayerExtraGeom
    extra = 0


class CrudLayerAdmin(VersionAdmin):
    list_display = ('pk', 'name', 'geom_type', 'layer_groups')
    list_filter = ('geom_type', 'layer_groups')
    search_fields = ('pk', 'name')
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }
    inlines = [LayerExtraGeomInline, ]
    readonly_fields = ('schema', )  # schema is managed with crud view properties


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


class FeatureExtraGeomInline(admin.TabularInline):
    classes = ('collapse', )
    verbose_name = _('Extra geometry')
    verbose_name_plural = _('Extra geometries')
    model = FeatureExtraGeom
    form = forms.FeatureExtraGeomForm
    extra = 0


class CrudFeatureAdmin(VersionAdmin, OSMGeoAdmin):
    list_max_show_all = 50
    list_display = ('pk', 'identifier', 'layer', 'source', 'target')
    list_filter = ('layer', )
    search_fields = ('pk', 'identifier', )
    inlines = (FeatureExtraGeomInline, FeaturePictureInline, FeatureAttachmentInline)
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }


class AttachmentCategoryAdmin(VersionAdmin):
    list_display = ('pk', 'name', 'pictogram')
    search_fields = ('pk', 'name', )
