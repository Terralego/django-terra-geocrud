from django.contrib import admin
from . import models


@admin.register(models.CrudGroupView)
class CrudGroupViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram']


class FeatureDisplayGroupTabularInline(admin.TabularInline):
    model = models.FeaturePropertyDisplayGroup


@admin.register(models.CrudView)
class CrudViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram', 'properties']
    list_filter = ['group', ]
    inlines = [FeatureDisplayGroupTabularInline, ]
