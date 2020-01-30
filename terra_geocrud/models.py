from copy import deepcopy

from django.contrib.gis.db.models import Extent
from django.contrib.postgres.fields import JSONField, ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from geostore.db.mixins import BaseUpdatableModel
from sorl.thumbnail import ImageField, get_thumbnail

from . import settings as app_settings
from .properties.schema import FormSchemaMixin
from terra_geocrud.map.styles import MapStyleModelMixin
from .properties.files import get_storage
from .properties.widgets import get_widgets_choices


class CrudModelMixin(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text=_("Display name in left menu"))
    order = models.PositiveSmallIntegerField(help_text=_("Order entry in left menu"), db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class CrudGroupView(CrudModelMixin):
    """
    Used to defined group of view in CRUD
    """
    pictogram = models.ImageField(upload_to='crud/groups/pictograms', null=True, blank=True,
                                  help_text=_("Picto displayed in left menu"))

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ('order', )


class CrudView(FormSchemaMixin, MapStyleModelMixin, CrudModelMixin):
    """
    Used to defined ad layer's view in CRUD
    """
    group = models.ForeignKey(CrudGroupView, on_delete=models.SET_NULL, related_name='crud_views',
                              null=True, blank=True, help_text=_("Group this entry in left menu"))
    layer = models.OneToOneField('geostore.Layer', on_delete=models.CASCADE, related_name='crud_view')
    templates = models.ManyToManyField('template_model.Template', related_name='crud_views', blank=True,
                                       help_text=_("Available templates for layer features document generation"))
    pictogram = models.ImageField(upload_to='crud/views/pictograms', null=True, blank=True,
                                  help_text=_("Picto displayed in left menu"))
    map_style = JSONField(default=dict, blank=True, help_text=_("Custom mapbox style for this entry"))
    # WARNING: settings is only used to wait for model definition
    settings = JSONField(default=dict, blank=True)
    default_list_properties = models.ManyToManyField('geostore.LayerSchemaProperty', related_name='crud_views',
                                                     blank=True, help_text=_("Default list of properties for a view"))
    feature_title_property = models.ForeignKey('geostore.LayerSchemaProperty',
                                               help_text=_("Schema property used to define feature title."), blank=True,
                                               null=True, on_delete=models.SET_NULL)
    visible = models.BooleanField(default=True, db_index=True, help_text=_("Keep visible if ungrouped."))

    @cached_property
    def extent(self):
        features_extent = self.layer.features.aggregate(extent=Extent('geom'))
        extent = features_extent.get('extent')
        # get extent in settings if no features

        return extent if extent else app_settings.TERRA_GEOCRUD['EXTENT']

    def get_layer(self):
        return self.layer

    @property
    def generated_ui_schema(self):
        """ Generate JSON schema according to linked schema properties  """
        ui_schema_properties = self.ui_schema_properties.all().order_by('order').prefetch_related('ui_array_properties')
        ui_schema = {}
        ui_order = []
        for prop in ui_schema_properties:
            name = prop.layer_schema.slug
            if prop.schema:
                ui_schema.update({name: prop.schema})
            ui_array_order = []
            if prop.order:
                ui_order.append(name)
            for prop_array in prop.ui_array_properties.all().order_by('order'):
                name_array = prop_array.array_layer_schema.slug
                ui_schema.setdefault(name, {})
                ui_schema[name].setdefault('items', {})
                if prop_array.schema:
                    ui_schema[name]['items'].update({name_array: prop_array.schema})
                if prop_array.order:
                    ui_array_order.append(name_array)
            if ui_array_order:
                ui_schema[name].setdefault('items', {})
                ui_schema[name]['items'].update({'ui:order': ui_array_order})
        ui_order.append('*')
        if ui_order:
            ui_schema.update({'ui:order': ui_order})
        return ui_schema

    class Meta:
        verbose_name = _("View")
        verbose_name_plural = _("Views")
        ordering = ('group', 'order')


class FeaturePropertyDisplayGroup(models.Model):
    """ Model used to group layer properties in grouped_form_schema and displayed informations """
    crud_view = models.ForeignKey(CrudView, related_name='feature_display_groups', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    label = models.CharField(max_length=50)
    slug = models.SlugField(blank=True, editable=False)
    pictogram = models.ImageField(upload_to='crud/feature_display_group/pictograms', null=True, blank=True)
    properties = ArrayField(models.CharField(max_length=250), default=list)

    def __str__(self):
        return self.label

    @cached_property
    def form_schema(self):
        original_schema = deepcopy(self.crud_view.layer.generated_schema)
        properties = {}
        required = []

        for prop in list(self.properties):
            properties[prop] = original_schema['properties'][prop]

            if prop in original_schema.get('required', []):
                required.append(prop)

        return {
            "type": "object",
            "title": self.label,
            "required": required,
            "properties": properties
        }

    class Meta:
        verbose_name = _("Feature properties display group")
        verbose_name_plural = _("Feature properties display groups")
        ordering = ('order', 'label',)
        unique_together = (
            ('crud_view', 'label'),
            ('crud_view', 'slug'),
        )

    def clean(self):
        # verify properties exists
        unexpected_properties = list(set(self.properties) - set(self.crud_view.properties))
        if unexpected_properties:
            raise ValidationError(f'Properties should exists : {unexpected_properties}')

    def save(self, *args, **kwargs):
        # generate slug
        self.slug = slugify(self.label)

        super().save(*args, **kwargs)


class PropertyDisplayRendering(models.Model):
    crud_view = models.ForeignKey(CrudView, related_name='feature_property_rendering', on_delete=models.CASCADE)
    property = models.CharField(max_length=255, blank=False, null=False)
    widget = models.CharField(max_length=255, choices=get_widgets_choices())
    args = JSONField(default=dict, blank=True)

    def clean(self):
        # verify property exists
        if self.property not in self.crud_view.properties:
            raise ValidationError(f'Property should exists in layer schema definition : {self.property}')

    class Meta:
        verbose_name = _("Custom feature property rendering")
        verbose_name_plural = _("Custom feature properties rendering")
        ordering = ('crud_view', 'property',)
        unique_together = (
            ('crud_view', 'property'),
        )


class AttachmentCategory(models.Model):
    name = models.CharField(unique=True, max_length=255)
    pictogram = models.ImageField(upload_to='crud/attachments_category/pictograms', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Attachment category')
        verbose_name_plural = _('Attachment categories')


class AttachmentMixin(BaseUpdatableModel):
    category = models.ForeignKey(AttachmentCategory, on_delete=models.PROTECT)
    legend = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.legend} - ({self.category})"

    class Meta:
        abstract = True


def feature_attachment_directory_path(instance, filename):
    return f'terra_geocrud/features/{instance.feature_id}/attachments/{filename}'


def feature_picture_directory_path(instance, filename):
    return f'terra_geocrud/features/{instance.feature_id}/pictures/{filename}'


class FeatureAttachment(AttachmentMixin):
    feature = models.ForeignKey('geostore.Feature', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=feature_attachment_directory_path, storage=get_storage())

    class Meta:
        verbose_name = _('Feature attachment')
        verbose_name_plural = _('Feature attachments')
        ordering = (
            'feature', 'category', '-updated_at'
        )


class FeaturePicture(AttachmentMixin):
    feature = models.ForeignKey('geostore.Feature', on_delete=models.CASCADE, related_name='pictures')
    image = ImageField(upload_to=feature_picture_directory_path, storage=get_storage())

    @cached_property
    def thumbnail(self):
        return get_thumbnail(self.image, '350x250', crop='noop', quality=90)

    class Meta:
        verbose_name = _('Feature picture')
        verbose_name_plural = _('Feature pictures')
        ordering = (
            'feature', 'category', '-updated_at'
        )


class ExtraLayerStyle(MapStyleModelMixin, models.Model):
    crud_view = models.ForeignKey(CrudView, related_name='extra_layer_style', on_delete=models.CASCADE)
    layer_extra_geom = models.OneToOneField('geostore.LayerExtraGeom', related_name='style', on_delete=models.CASCADE)
    map_style = JSONField(help_text=_("Custom mapbox style for this entry"))

    def get_layer(self):
        return self.layer_extra_geom

    class Meta:
        verbose_name = _('ExtraLayer style')
        verbose_name_plural = _('ExtraLayer styles')
        unique_together = (
            ('crud_view', 'layer_extra_geom'),
        )


class UISchemaObjectProperty(models.Model):
    schema = JSONField(help_text=_("Custom ui schema"), blank=True, default=dict)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True


class UISchemaProperty(UISchemaObjectProperty):
    crud_view = models.ForeignKey(CrudView, related_name='ui_schema_properties', on_delete=models.PROTECT)
    layer_schema = models.OneToOneField('geostore.LayerSchemaProperty',
                                        related_name='ui_schema_property',
                                        on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.crud_view}: {self.layer_schema.slug} ({self.layer_schema.prop_type})"

    class Meta:
        verbose_name = _("UI Schema property")
        verbose_name_plural = _("UI Schema properties")


class UIArraySchemaProperty(UISchemaObjectProperty):
    ui_schema_property = models.ForeignKey(UISchemaProperty, related_name='ui_array_properties',
                                           on_delete=models.PROTECT)
    array_layer_schema = models.OneToOneField('geostore.ArrayObjectProperty',
                                              related_name='ui_array_schema',
                                              on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.ui_schema_property}: {self.array_layer_schema.slug} ({self.array_layer_schema.prop_type})"

    class Meta:
        verbose_name = _("UI Array object schema property")
        verbose_name_plural = _("UI Array object schema properties")
