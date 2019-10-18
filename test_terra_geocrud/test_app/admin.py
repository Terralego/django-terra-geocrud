from django.contrib import admin

from geostore.models import Layer, Feature
from terra_geocrud import admin as geocrud_admin
from terra_geocrud import models

admin.site.register(models.CrudGroupView, geocrud_admin.CrudGroupViewAdmin)
admin.site.register(models.CrudView, geocrud_admin.CrudViewAdmin)
admin.site.register(models.AttachmentCategory, geocrud_admin.AttachmentCategoryAdmin)
admin.site.register(Layer, geocrud_admin.CrudLayerAdmin)
admin.site.register(Feature, geocrud_admin.CrudFeatureAdmin)
