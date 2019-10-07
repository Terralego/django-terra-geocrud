from django.contrib.gis.db.models import Extent
from django.contrib.postgres.fields import JSONField, ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from terra_geocrud.properties.widgets import get_widgets_choices
from . import settings as app_settings


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


class CrudView(CrudModelMixin):
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
    ui_schema = JSONField(default=dict, blank=True,
                          help_text=_("""Custom ui:schema style for this entry.
                                         https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/"""))
    # WARNING: settings is only used to wait for model definition
    settings = JSONField(default=dict, blank=True)
    default_list_properties = ArrayField(models.CharField(max_length=250), default=list, blank=True)

    def clean(self):
        # verify properties exists
        unexpected_properties = list(set(self.default_list_properties) - set(self.list_available_properties))
        if unexpected_properties:
            raise ValidationError(f'Properties should exists and available for feature list : {unexpected_properties}')

    @property
    def form_schema(self):
        original_schema = self.layer.schema.copy()
        generated_schema = original_schema.copy()
        groups = self.feature_display_groups.all()
        processed_properties = []
        generated_schema['properties'] = {}

        for group in groups:
            # group properties by sub object, then add other properties
            generated_schema['properties'][group.slug] = group.form_schema
            processed_properties += list(group.properties)
            for prop in group.properties:
                try:
                    generated_schema.get('required', []).remove(prop)
                except ValueError:
                    pass
        # add default other properties
        remained_properties = list(set(self.properties) - set(processed_properties))
        for prop in remained_properties:
            generated_schema['properties'][prop] = original_schema['properties'][prop]

        return generated_schema

    @property
    def properties(self):
        return sorted(list(self.layer.layer_properties.keys())) if self.layer else []

    @property
    def list_available_properties(self):
        """ exclude some properties in list (some arrays, data-url, html fields)"""
        properties = []

        for prop in self.properties:
            # exclude format 'data-url', array if final data is object, and textarea / rte fields
            if (self.layer.schema.get('properties', {}).get(prop).get('format') != 'data-url') and (
                    self.layer.schema.get('properties', {}).get(prop).get('type') != 'array'
                    or self.layer.schema.get('properties', {}).get(prop).get('items', {}).get('type') != 'object')\
                    and (self.ui_schema.get(prop, {}).get('ui:widget') != 'textarea'
                         and self.ui_schema.get(prop, {}).get('ui:field') != 'rte'):
                properties.append(prop)
        return properties

    @property
    def extent(self):
        features_extent = self.layer.features.aggregate(extent=Extent('geom'))
        # get extent in settings if no features
        return features_extent.get('extent',
                                   app_settings.TERRA_GEOCRUD['EXTENT'])

    def render_property_data(self, feature, property_key):
        """ if custom rendering widget defined for property, apply widget """
        custom_widget_rendering = self.feature_property_rendering.filter(property=property_key).first()

        if custom_widget_rendering:
            module_name, unit_name = custom_widget_rendering.widget.rsplit('.', 1)
            WidgetClass = getattr(__import__(module_name, fromlist=['']), unit_name)
            widget = WidgetClass(feature=feature, property=property_key, args=custom_widget_rendering.args)
            return widget.render()

        return feature.properties.get(property_key)

    class Meta:
        verbose_name = _("View")
        verbose_name_plural = _("Views")
        ordering = ('order',)


class FeaturePropertyDisplayGroup(models.Model):
    """ Model used to group layer properties in form_schema and displayed informations """
    crud_view = models.ForeignKey(CrudView, related_name='feature_display_groups', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    label = models.CharField(max_length=50)
    slug = models.SlugField(blank=True, editable=False)
    pictogram = models.ImageField(upload_to='crud/feature_display_group/pictograms', null=True, blank=True)
    properties = ArrayField(models.CharField(max_length=250), default=list)

    def __str__(self):
        return self.label

    @property
    def form_schema(self):
        original_schema = self.crud_view.layer.schema.copy()
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
