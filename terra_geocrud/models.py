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

from terra_geocrud.map.styles import MapStyleModelMixin
from . import settings as app_settings
from .properties.files import get_storage
from .properties.schema import FormSchemaMixin


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
    ui_schema = JSONField(default=dict, blank=True,
                          help_text=_("""Custom ui:schema style for this entry.
                                         https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/"""))
    # WARNING: settings is only used to wait for model definition
    settings = JSONField(default=dict, blank=True)
    default_list_properties = ArrayField(models.CharField(max_length=250), default=list, blank=True)
    feature_title_property = models.CharField(help_text=_("Schema property used to define feature title."),
                                              max_length=250, blank=True, null=False, default="")
    visible = models.BooleanField(default=True, db_index=True, help_text=_("Keep visible if ungrouped."))

    @cached_property
    def extent(self):
        features_extent = self.layer.features.aggregate(extent=Extent('geom'))
        extent = features_extent.get('extent')
        # get extent in settings if no features

        return extent if extent else app_settings.TERRA_GEOCRUD['EXTENT']

    def get_layer(self):
        return self.layer

    def get_feature_title(self, feature):
        """ Get feature title base on title field. Return identifier if empty or None """
        return feature.properties.get(self.feature_title_property, '')\
            if self.feature_title_property else feature.identifier

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
        original_schema = deepcopy(self.crud_view.layer.schema)
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
