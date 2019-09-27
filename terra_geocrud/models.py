from django.contrib.postgres.fields import JSONField, ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class CrudModelMixin(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class CrudGroupView(CrudModelMixin):
    """
    Used to defined group of view in CRUD
    """
    pictogram = models.ImageField(upload_to='crud/groups/pictograms', null=True, blank=True)

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ('order', )


class CrudView(CrudModelMixin):
    """
    Used to defined ad layer's view in CRUD
    """
    group = models.ForeignKey(CrudGroupView, on_delete=models.SET_NULL, related_name='crud_views',
                              null=True, blank=True)
    layer = models.OneToOneField('geostore.Layer', on_delete=models.CASCADE, related_name='crud_view')
    templates = models.ManyToManyField('template_model.Template', related_name='crud_views', blank=True)
    pictogram = models.ImageField(upload_to='crud/views/pictograms', null=True, blank=True)
    map_style = JSONField(default=dict, blank=True)
    ui_schema = JSONField(default=dict, blank=True,
                          help_text="https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/")
    # WARNING: settings is only used to wait for model definition
    settings = JSONField(default=dict, blank=True)

    @property
    def form_schema(self):
        """
        Crud's view custom json form schema
        """
        original_schema = self.layer.schema.copy()
        # TODO: improve schema with custom select from generic foreign key, allowing selecting model from final apps
        return original_schema

    @property
    def properties(self):
        return sorted(list(self.layer.layer_properties.keys()))

    class Meta:
        verbose_name = _("View")
        verbose_name_plural = _("Views")
        ordering = ('order',)


class FeaturePropertyDisplayGroup(models.Model):
    crud_view = models.ForeignKey(CrudView, related_name='feature_display_groups', on_delete=models.CASCADE)
    label = models.CharField(max_length=50)
    slug = models.SlugField(blank=True)
    pictogram = models.ImageField(upload_to='crud/feature_display_group/pictograms', null=True, blank=True)
    properties = ArrayField(models.CharField(max_length=250), default=list)

    class Meta:
        verbose_name = _("Display Group")
        verbose_name_plural = _("Display Groups")
        ordering = ('label',)
        unique_together = (
            ('crud_view', 'label'),
            ('crud_view', 'slug'),
        )

    def clean(self):
        # verify properties exists
        if list(set(self.properties) - set(self.crud_view.properties)) != []:
            raise ValidationError('Properties should exists')

    def save(self, *args, **kwargs):
        # generate slug
        self.slug = slugify(self.label)

        super().save(*args, **kwargs)
