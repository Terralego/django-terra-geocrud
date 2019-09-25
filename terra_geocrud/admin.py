from django.contrib import admin
from . import models


@admin.register(models.CrudGroupView)
class CrudGroupViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram']


@admin.register(models.CrudView)
class CrudViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'pictogram']
    list_filter = ['group', ]
