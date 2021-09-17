from copy import deepcopy

from django.contrib.gis.db.models import Extent
from django.core.exceptions import ValidationError
from django.db.models import FloatField, CharField, IntegerField
from django.db.models.functions import Cast

try:
    from django.db.models import JSONField
except ImportError:  # TODO: Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import CheckConstraint, UniqueConstraint, Q
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from geostore.db.mixins import BaseUpdatableModel
from sorl.thumbnail import ImageField, get_thumbnail, delete

from terra_geocrud.map.styles import MapStyleModelMixin
from . import settings as app_settings
from .properties.files import get_storage
from .properties.schema import FormSchemaMixin
from .validators import validate_schema_property, validate_function_path


class CrudModelMixin(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text=_("Display name in left menu"),
                            verbose_name=_('Name'))
    order = models.PositiveSmallIntegerField(verbose_name=_("Order"),
                                             help_text=_("Order entry in left menu"), db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class CrudGroupView(CrudModelMixin):
    """
    Used to defined group of view in CRUD
    """
    pictogram = models.ImageField(upload_to='terra_geocrud/groups/pictograms', null=True, blank=True,
                                  help_text=_("Picto displayed in left menu"))

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ('order', )


class CrudView(FormSchemaMixin, MapStyleModelMixin, CrudModelMixin):
    """
    Used to defined ad layer's view in CRUD
    """
    object_name = models.CharField(verbose_name=_("Singular object name"), max_length=100, default="",
                                   blank=True, null=False)
    object_name_plural = models.CharField(verbose_name=_("Plural object name"), max_length=100, default="",
                                          blank=True, null=False)
    group = models.ForeignKey(CrudGroupView, verbose_name=_("Group"), on_delete=models.SET_NULL,
                              related_name='crud_views',
                              null=True, blank=True, help_text=_("Group this entry in left menu"))
    layer = models.OneToOneField('geostore.Layer', on_delete=models.CASCADE, related_name='crud_view',
                                 verbose_name=_("Layer"))
    templates = models.ManyToManyField('template_model.Template', related_name='crud_views', blank=True,
                                       verbose_name=_("Document templates"),
                                       help_text=_("Available templates for layer features document generation"))
    pictogram = models.ImageField(upload_to='terra_geocrud/views/pictograms', null=True, blank=True,
                                  help_text=_("Picto displayed in left menu"))
    map_style = JSONField(default=dict, blank=True, help_text=_("Custom mapbox style for this entry"),
                          verbose_name=_("Map style"))
    ui_schema = JSONField(default=dict, blank=True, editable=False,
                          help_text=_("""Custom ui:schema style for this entry.
                                         https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/"""))
    # WARNING: settings is only used to wait for model definition
    settings = JSONField(default=dict, blank=True)
    default_list_properties = models.ManyToManyField('CrudViewProperty', verbose_name=_("Properties in feature list"),
                                                     blank=True, related_name='used_by_list',
                                                     help_text=_("Schema properties used in API list by default."),)
    feature_title_property = models.ForeignKey('CrudViewProperty', null=True, on_delete=models.SET_NULL,
                                               verbose_name=_("Title property"),
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
    pictogram = models.ImageField(upload_to='terra_geocrud/property_groups/pictograms', null=True, blank=True)

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
    pictogram = models.ImageField(upload_to='terra_geocrud/attachments_categories/pictograms', null=True, blank=True)

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
    include_in_tile = models.BooleanField(default=False, db_index=True)
    required = models.BooleanField(default=False, db_index=True)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)

    """ This field is used to order properties in a table view """
    table_order = models.PositiveSmallIntegerField(null=True, blank=True, db_index=False)
    editable = models.BooleanField(default=True)
    function_path = models.CharField(max_length=255, blank=True, validators=[validate_function_path])

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
        constraints = [
            CheckConstraint(check=(
                Q(required=True, editable=True)
                | Q(required=False, editable=True)
                | Q(required=False, editable=False)),
                name='check_required_editable'),
        ]

    def __str__(self):
        return f"{self.title} ({self.key})"

    def clean(self):
        if self.required and not self.editable:
            raise ValidationError(
                _("Property cannot be required but not editable")
            )

    @property
    def title(self):
        """ Title: ui schema -> json schema -> key capitalized """
        return self.ui_schema.get('title',
                                  self.json_schema.get('title',
                                                       self.key.capitalize()))

    @cached_property
    def full_json_schema(self):
        """
        Generate full json schema by adding custom conf to store schema.
        All keys defined in json_schema column are kept if already present.
        """
        output_field = CharField()
        if self.json_schema.get("type") == "number" or (
                self.json_schema.get("type") == "array" and self.json_schema.get("items").get("type") == "number"):
            # final values should be float
            output_field = FloatField()
        elif self.json_schema.get("type") == "integer" or (
                self.json_schema.get("type") == "array" and self.json_schema.get("items").get("type") == "integer"):
            # final values should be integer
            output_field = IntegerField()
        values = self.values.all().annotate(final_value=Cast('value', output_field=output_field))
        if values:
            json_schema = deepcopy(self.json_schema)
            if self.json_schema.get('type') != "array":
                # in non array properties, enum are defined in enum key
                json_schema.setdefault('enum', list(values.values_list('final_value', flat=True)))
            else:
                # in array, enum values are defined in 'items__enum' key
                json_schema['items'].setdefault('enum', list(values.values_list('final_value', flat=True)))
            return json_schema
        return self.json_schema


class PropertyEnum(models.Model):
    value = models.CharField(max_length=250, help_text=_("Value should always be casted in property type."))
    pictogram = models.ImageField(upload_to='terra_geocrud/enums/pictograms', null=True, blank=True,
                                  help_text=_("Picto. associated to value."))
    property = models.ForeignKey(CrudViewProperty, on_delete=models.CASCADE, related_name='values')

    def clean(self):
        try:
            if self.property.json_schema.get('type') == 'integer':
                int(self.value)
            elif self.property.json_schema.get('type') == 'number':
                float(self.value)
        except ValueError:
            raise ValidationError(
                _(f"Value '{self.value}' should be casted as property type ({self.property.json_schema.get('type')})")
            )

    def __str__(self):
        return self.value

    class Meta:
        unique_together = (
            ('value', 'property'),
        )


class RoutingSettings(models.Model):
    CHOICES_EXTERNAL = (("mapbox", _("Mapbox")), )
    CHOICES = CHOICES_EXTERNAL + (("geostore", _("Geostore")), )
    label = models.CharField(max_length=250, help_text=_("Label that will be shown on the list"))
    provider = models.CharField(max_length=250, help_text=_("Provider's name"), choices=CHOICES)
    layer = models.ForeignKey('geostore.Layer', related_name='routing_settings', on_delete=models.PROTECT, blank=True,
                              null=True)
    mapbox_transit = models.CharField(max_length=250, help_text=_("Mabox transit"), choices=(("driving", _("Driving")),
                                                                                             ("walking", _("Walking")),
                                                                                             ("cycling", _("Cycling"))
                                                                                             ), blank=True)
    crud_view = models.ForeignKey(CrudView, related_name='routing_settings', on_delete=models.CASCADE)

    def __str__(self):
        return self.label

    class Meta:
        unique_together = (
            ('label', 'crud_view'),
            ('layer', 'crud_view'),
        )
        constraints = [
            UniqueConstraint(fields=['provider', 'layer', 'crud_view'], condition=Q(layer__isnull=False),
                             name='check_provider_layer'
                             ),
            UniqueConstraint(fields=['provider', 'mapbox_transit', 'crud_view'], condition=~Q(mapbox_transit=''),
                             name='check_provider_mapbox_transit'
                             ),
        ]

    def clean(self):
        if self.layer and not self.layer.routable:
            raise ValidationError(
                _("You should define layer with a routable layer")
            )
        if self.mapbox_transit and self.layer:
            raise ValidationError(
                _("You shouldn't define layer and mapbox_transit")
            )
        if self.provider == "mapbox" and self.layer or self.provider == "geostore" and self.mapbox_transit:
            raise ValidationError(
                _("You use the wrong provider")
            )
        if self.provider == "mapbox" and not self.mapbox_transit:
            raise ValidationError(
                _("You should define a mapbox_transit with this provider")
            )
        if self.provider == "geostore" and not self.layer:
            raise ValidationError(
                _("You should define a layer with this provider")
            )
        if RoutingSettings.objects.filter(Q(mapbox_transit=self.mapbox_transit) & ~Q(mapbox_transit=''),
                                          crud_view=self.crud_view).exclude(label=self.label):
            raise ValidationError(
                _("This transit is already used")
            )
        if RoutingSettings.objects.filter(Q(layer=self.layer) & Q(layer__isnull=False),
                                          crud_view=self.crud_view).exclude(label=self.label):
            raise ValidationError(
                _("This layer is already used")
            )


class RoutingInformations(models.Model):
    feature = models.OneToOneField('geostore.Feature', on_delete=models.CASCADE,
                                   related_name='routing_information')
    route_description = JSONField(blank=True, null=False, default=dict)

    def __str__(self):
        return f"Routing infos : {self.feature.identifier}"
