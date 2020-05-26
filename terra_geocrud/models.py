from copy import deepcopy

from django.contrib.gis.db.models import Extent
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from geostore.db.mixins import BaseUpdatableModel
from sorl.thumbnail import ImageField, get_thumbnail, delete

from terra_geocrud.map.styles import MapStyleModelMixin
from . import settings as app_settings
from .properties.files import get_storage
from .properties.schema import FormSchemaMixin
from .validators import validate_schema_property


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
    object_name = models.CharField(max_length=100, default="", blank=True, null=False)
    object_name_plural = models.CharField(max_length=100, default="", blank=True, null=False)
    group = models.ForeignKey(CrudGroupView, on_delete=models.SET_NULL, related_name='crud_views',
                              null=True, blank=True, help_text=_("Group this entry in left menu"))
    layer = models.OneToOneField('geostore.Layer', on_delete=models.CASCADE, related_name='crud_view')
    templates = models.ManyToManyField('template_model.Template', related_name='crud_views', blank=True,
                                       help_text=_("Available templates for layer features document generation"))
    pictogram = models.ImageField(upload_to='crud/views/pictograms', null=True, blank=True,
                                  help_text=_("Picto displayed in left menu"))
    map_style = JSONField(default=dict, blank=True, help_text=_("Custom mapbox style for this entry"))
    ui_schema = JSONField(default=dict, blank=True, editable=False,
                          help_text=_("""Custom ui:schema style for this entry.
                                         https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/"""))
    # WARNING: settings is only used to wait for model definition
    settings = JSONField(default=dict, blank=True)
    default_list_properties = models.ManyToManyField('CrudViewProperty', blank=True, related_name='used_by_list',
                                                     help_text=_("Schema properties used in API list by default."),)
    feature_title_property = models.ForeignKey('CrudViewProperty', null=True, on_delete=models.SET_NULL,
                                               help_text=_("Schema property used to define feature title."),
                                               related_name='used_by_title', blank=True)
    visible = models.BooleanField(default=True, db_index=True, help_text=_("Keep visible if ungrouped."))

    @cached_property
    def extent(self):
        features_extent = self.layer.features.aggregate(extent=Extent('geom'))
        extent = features_extent.get('extent')
        # get extent in settings if no features

        return extent if extent else app_settings.TERRA_GEOCRUD['EXTENT']

    @property
    def list_available_properties(self):
        """ exclude some properties in list (some arrays, data-url, html fields)"""
        # exclude file field
        properties = self.properties.exclude(
            json_schema__contains={"format": 'data-url'},
        )
        # exclude array object fields

        properties = properties.exclude(
            json_schema__contains={"type": "array", "items": {"type": "object"}}
        )
        # exclude textarea fields
        properties = properties.exclude(
            ui_schema__contains={'ui:widget': 'textarea'}
        )
        # exclude rte fields
        properties = properties.exclude(
            ui_schema__contains={'ui:field': 'rte'}
        )
        return properties

    def get_layer(self):
        return self.layer

    def get_feature_title(self, feature):
        """ Get feature title base on title field. Return identifier if empty or None """
        data = feature.properties.get(self.feature_title_property.key, '')\
            if self.feature_title_property else feature.identifier
        return data or feature.identifier

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

    def __str__(self):
        return self.label

    @cached_property
    def form_schema(self):
        original_schema = deepcopy(self.crud_view.layer.schema)
        properties = {}
        required = []

        for prop in self.group_properties.all():
            properties[prop.key] = original_schema.get('properties', {}).get(prop.key)

            if prop.key in original_schema.get('required', []):
                required.append(prop.key)

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

    def save(self, *args, **kwargs):
        # generate slug
        self.slug = slugify(self.label)

        super().save(*args, **kwargs)


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

    def delete(self, *args, **kwargs):
        """ Delete file at deletion """
        self.file.storage.delete(self.file.name)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = _('Feature attachment')
        verbose_name_plural = _('Feature attachments')
        ordering = (
            'feature', 'category', '-created_at'
        )


class FeaturePicture(AttachmentMixin):
    feature = models.ForeignKey('geostore.Feature', on_delete=models.CASCADE, related_name='pictures')
    image = ImageField(upload_to=feature_picture_directory_path, storage=get_storage())

    @cached_property
    def thumbnail(self):
        return get_thumbnail(self.image, "500x500", crop='noop', upscale=False)

    def delete(self, *args, **kwargs):
        """ Delete image and thumbnail at deletion """
        self.image.storage.delete(self.image.name)
        delete(self.image)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = _('Feature picture')
        verbose_name_plural = _('Feature pictures')
        ordering = (
            'feature', 'category', '-created_at'
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


class CrudViewProperty(models.Model):
    view = models.ForeignKey(CrudView, on_delete=models.CASCADE, related_name='properties')
    group = models.ForeignKey(FeaturePropertyDisplayGroup, on_delete=models.SET_NULL,
                              related_name='group_properties', null=True, blank=True)
    key = models.SlugField()
    json_schema = JSONField(blank=False, null=False, default=dict, validators=[validate_schema_property])
    ui_schema = JSONField(blank=True, null=False, default=dict)
    required = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta:
        unique_together = (
            ('view', 'key'),
        )
        ordering = (
            'view', 'group', 'order'
        )
        indexes = (
            GinIndex(name='json_schema_index', fields=['json_schema'], opclasses=['jsonb_path_ops']),
            GinIndex(name='ui_schema_index', fields=['ui_schema'], opclasses=['jsonb_path_ops']),
        )

    def __str__(self):
        return f"{self.title} ({self.key})"

    @property
    def title(self):
        """ Title: ui schema -> json schema -> key capitalized """
        return self.ui_schema.get('title',
                                  self.json_schema.get('title',
                                                       self.key.capitalize()))

    def delete(self, **kwargs):
        super().delete(**kwargs)

        # delete feature property keys
        fs = self.view.layer.features.all()
        for f in fs:
            f.properties.pop(self.key, None)
            f.save()
