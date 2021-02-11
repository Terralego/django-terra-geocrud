from nested_admin.nested import NestedModelAdmin, NestedTabularInline

try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
import admin_thumbnails
from admin_ordering.admin import OrderableAdmin
from django.contrib import admin, messages
from django.contrib.gis.admin import OSMGeoAdmin
from django.utils.translation import gettext_lazy as _
from django_json_widget.widgets import JSONEditorWidget
from django_object_actions import DjangoObjectActions
from geostore.models import LayerExtraGeom, LayerRelation, FeatureExtraGeom
from reversion.admin import VersionAdmin
from sorl.thumbnail.admin import AdminInlineImageMixin

from . import models, forms
from .properties.schema import sync_layer_schema, sync_ui_schema, clean_properties_not_in_schema_or_null, \
    sync_properties_in_tiles


@admin_thumbnails.thumbnail('pictogram')
class CrudGroupViewAdmin(OrderableAdmin, VersionAdmin):
    ordering_field = "order"
    list_editable = ["order"]
    list_display = ['name', 'order', 'pictogram_thumbnail']


@admin_thumbnails.thumbnail('pictogram')
class FeatureDisplayGroupTabularInline(OrderableAdmin, NestedTabularInline):
    ordering_field = "order"
    classes = ('collapse', )
    verbose_name = _('Display group')
    verbose_name_plural = _('Display groups for feature property display and form.')
    model = models.FeaturePropertyDisplayGroup
    extra = 0


class ExtraLayerStyleInLine(NestedTabularInline):
    classes = ('collapse', )
    verbose_name = _('Extra layer style')
    verbose_name_plural = _('Extra layer styles')
    model = models.ExtraLayerStyle
    form = forms.ExtraLayerStyleForm
    extra = 0
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget},
    }


@admin_thumbnails.thumbnail('pictogram')
class PropertyEnumInline(NestedTabularInline):
    model = models.PropertyEnum
    extra = 0
    classes = ('collapse', )
    verbose_name = _("Value")
    verbose_name_plural = _("Available values. Let empty if you want to let free input.")


class CrudPropertyInline(OrderableAdmin, NestedTabularInline):
    ordering_field = "order"
    classes = ('collapse', )
    verbose_name = _("Feature property")
    verbose_name_plural = _("Feature properties")
    model = models.CrudViewProperty
    form = forms.CrudPropertyForm
    extra = 0
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget(height=200)},
    }
    inlines = [PropertyEnumInline, ]


class RoutingSettingsInLine(NestedTabularInline):
    classes = ('collapse',)
    verbose_name = _('Routing setting')
    verbose_name_plural = _('Routing settings')
    model = models.RoutingSettings
    extra = 0
    form = forms.RoutingSettingsForm


@admin_thumbnails.thumbnail('pictogram')
class CrudViewAdmin(OrderableAdmin, DjangoObjectActions, VersionAdmin, NestedModelAdmin):
    ordering_field = "order"
    list_editable = ["order"]
    filter_horizontal = ('default_list_properties', )
    form = forms.CrudViewForm
    list_display = ['name', 'group', 'order', 'pictogram_thumbnail']
    list_filter = ['group', ]
    inlines = [FeatureDisplayGroupTabularInline, CrudPropertyInline, ExtraLayerStyleInLine, RoutingSettingsInLine]
    readonly_fields = ('ui_schema', )
    fieldsets = (
        (None, {'fields': (('name', 'object_name', 'object_name_plural', 'layer'), ('group', 'order', 'pictogram', 'pictogram_thumbnail'))}),
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
        JSONField: {'widget': JSONEditorWidget},
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

    def sync_tile_content(self, request, obj):
        sync_properties_in_tiles(obj)
        messages.success(request, _("Properties in tiles have been synced."))

    sync_tile_content.label = _("Define properties in tiles.")
    sync_tile_content.short_description = _("Define property marked as included in tile in layer definition..")

    change_actions = ('sync_schemas', 'clean_feature_properties', 'sync_tile_content')


class LayerExtraGeomInline(admin.TabularInline):
    model = LayerExtraGeom
    extra = 0


class LayerRelationInline(admin.TabularInline):
    verbose_name = _("Relation")
    verbose_name_plural = _("Relations")
    model = LayerRelation
    fk_name = 'origin'
    extra = 0


class CrudLayerAdmin(VersionAdmin):
    list_display = ('pk', 'name', 'geom_type', 'layer_groups')
    list_filter = ('geom_type', 'layer_groups')
    search_fields = ('pk', 'name')
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget},
    }
    inlines = [LayerExtraGeomInline, LayerRelationInline, ]
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
        JSONField: {'widget': JSONEditorWidget},
    }


@admin_thumbnails.thumbnail('pictogram')
class AttachmentCategoryAdmin(VersionAdmin):
    list_display = ('pk', 'name', 'pictogram_thumbnail')
    search_fields = ('pk', 'name', )
