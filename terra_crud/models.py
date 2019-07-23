from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _


class CrudMixin(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class CrudGroupView(CrudMixin):
    pictogram = models.ImageField(upload_to='crud/groups/pictograms')

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ('order', )


class CrudView(CrudMixin):
    group = models.ForeignKey(CrudGroupView, on_delete=models.PROTECT, related_name='crud_views')
    layer = models.OneToOneField('terra.Layer', on_delete=models.CASCADE, related_name='crud_view')
    pictogram = models.ImageField(upload_to='crud/views/pictograms')
    map_style = JSONField(default=dict)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("View")
        verbose_name_plural = _("Views")
        ordering = ('order',)
