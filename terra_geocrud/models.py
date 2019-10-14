from copy import deepcopy

from django.contrib.gis.db.models import Extent
from django.contrib.postgres.fields import JSONField, ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
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
    feature_title_property = models.CharField(help_text=_("Schema property used to define feature title."),
                                              max_length=250, blank=True, null=False, default="")

    def clean(self):
        # verify properties in default_list_properties exist
        unexpected_properties = list(set(self.default_list_properties) - set(self.list_available_properties))
        if unexpected_properties:
            raise ValidationError(f'Properties should exists for feature list : {unexpected_properties}')
        # verify feature_title_property exists
        if self.feature_title_property and self.feature_title_property not in self.properties:
            raise ValidationError(f'Property should exists for feature title : {self.feature_title_property}')

    @cached_property
    def grouped_form_schema(self):
        original_schema = deepcopy(self.layer.schema)
        generated_schema = deepcopy(original_schema)
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

    @cached_property
    def grouped_ui_schema(self):
        """
        Original ui_schema is recomposed with grouped properties
        """
        ui_schema = deepcopy(self.ui_schema)

        groups = self.feature_display_groups.all()
        for group in groups:
            # each field defined in ui schema should be placed in group key
            ui_schema[group.slug] = {'ui:order': []}

            for prop in group.properties:
                # get original definition
                original_def = ui_schema.pop(prop, None)
                if original_def:
                    ui_schema[group.slug][prop] = original_def

                # if original prop in ui:order
                if prop in ui_schema.get('ui:order', []):
                    ui_schema.get('ui:order').remove(prop)
                    ui_schema[group.slug]['ui:order'] += [prop]

            # finish by adding '*' in all cases (security)
            ui_schema[group.slug]['ui:order'] += ['*']
        if groups:
            ui_schema['ui:order'] = list(groups.values_list('slug', flat=True)) + ['*']
        return ui_schema

    @cached_property
    def properties(self):
        return sorted(list(self.layer.layer_properties.keys())) if self.layer else []

    @cached_property
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

    @cached_property
    def extent(self):
        features_extent = self.layer.features.aggregate(extent=Extent('geom'))
        extent = features_extent.get('extent')
        # get extent in settings if no features

        return extent if extent else app_settings.TERRA_GEOCRUD['EXTENT']

    class Meta:
        verbose_name = _("View")
        verbose_name_plural = _("Views")
        ordering = ('order',)
        permissions = [
            ("can_manage_views", _("Can create / edit / delete views / groups and associated layers.")),
            ("can_view_feature", _("Can read feature detail.")),
            ("can_add_feature", _("Can create feature")),
            ("can_change_feature", _("Can change feature")),
            ("can_delete_feature", _("Can delete feature")),
        ]


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
