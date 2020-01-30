from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.postgres import fields
from django.utils.translation import gettext_lazy as _
from geostore.models import LayerExtraGeom, LayerSchemaProperty, ArrayObjectProperty
from reversion.admin import VersionAdmin
from sorl.thumbnail.admin import AdminInlineImageMixin

from . import models, widgets


class ArrayObjectPropertyAdminInline(admin.TabularInline):
    model = ArrayObjectProperty
    extra = 1


class LayerSchemaPropertyAdmin(admin.ModelAdmin):
    inlines = [ArrayObjectPropertyAdminInline, ]
    extra = 1


class LayerSchemaPropertyAdminInline(admin.TabularInline):
    model = LayerSchemaProperty
    extra = 1


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


class PropertyDisplayRenderingTabularInline(admin.TabularInline):
    classes = ('collapse', )
    verbose_name = _('Custom widget')
    verbose_name_plural = _('Custom widgets for property content display rendering')
    model = models.PropertyDisplayRendering
    extra = 0


class UIArraySchemaPropertyAdminInline(admin.TabularInline):
    model = models.UIArraySchemaProperty
    extra = 1
    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }


class UISchemaPropertyAdmin(admin.ModelAdmin):
    inlines = [UIArraySchemaPropertyAdminInline, ]
    extra = 1
    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }
    list_filter = ['crud_view', ]
    list_display = ('crud_view', 'order', 'layer_schema')


class UISchemaPropertyAdminInline(admin.TabularInline):
    model = models.UISchemaProperty
    extra = 1


class CrudViewAdmin(VersionAdmin):
    list_display = ['name', 'order', 'pictogram', 'properties', ]
    list_filter = ['group', ]
    inlines = [FeatureDisplayGroupTabularInline, PropertyDisplayRenderingTabularInline, ExtraLayerStyleInLine,
               UISchemaPropertyAdminInline]
    readonly_fields = ['grouped_form_schema', 'properties']
    fieldsets = (
        (None, {'fields': (('name', 'layer'), ('group', 'order', 'pictogram'))}),
        (_('Properties'), {
            'fields': ('properties', 'default_list_properties', 'feature_title_property'),
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

    def add_view(self, request, form_url='', extra_context=None):
        self.obj = None
        return self.changeform_view(request, None, form_url, extra_context)

    def get_object(self, request, object_id, from_field=None):
        # Hook obj for use in formfield_for_manytomany and formfield_for_foreignkey
        self.obj = super(CrudViewAdmin, self).get_object(request, object_id)
        return self.obj

    def define_queryset_layer_schema(self, db_field, name):
        queryset = None
        if db_field.name == name:
            if self.obj:
                queryset = LayerSchemaProperty.objects.filter(layer=self.obj.layer)
            else:
                queryset = LayerSchemaProperty.objects.none()
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        kwargs["queryset"] = self.define_queryset_layer_schema(db_field, "feature_title_property")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        kwargs["queryset"] = self.define_queryset_layer_schema(db_field, "default_list_properties")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        ro_fields = super().get_readonly_fields(request, obj=obj)
        if obj and obj.pk:
            # dont change layer after creation
            ro_fields.append('layer')
        return ro_fields


class LayerExtraGeomInline(admin.TabularInline):
    model = LayerExtraGeom
    extra = 0


class CrudLayerAdmin(VersionAdmin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'geom_type', 'layer_groups')
    list_filter = ('geom_type', 'layer_groups')
    search_fields = ('pk', 'name')
    formfield_overrides = {
        fields.JSONField: {'widget': widgets.JSONEditorWidget},
    }
    inlines = [LayerExtraGeomInline, LayerSchemaPropertyAdminInline]


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
