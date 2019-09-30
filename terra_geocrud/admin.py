from django.contrib import admin

from . import models


@admin.register(models.CrudGroupView)
class CrudGroupViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram']


class FeatureDisplayGroupTabularInline(admin.TabularInline):
    model = models.FeaturePropertyDisplayGroup
    extra = 0


@admin.register(models.CrudView)
class CrudViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram', 'properties', ]
    list_filter = ['group', ]
    inlines = [FeatureDisplayGroupTabularInline, ]

    fieldsets = (
        (None, {'fields': (('name', 'layer'), ('group', 'order', 'pictogram'))}),
        ('Feature list', {'fields': ('properties', 'default_list_properties')}),
        ("Document generation", {'fields': ('templates', )}),
        ("Schema", {'fields': ('ui_schema', )}),
        ("Other settings", {'fields': (('map_style', 'settings'), )}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return ['layer', 'form_schema', 'properties']
