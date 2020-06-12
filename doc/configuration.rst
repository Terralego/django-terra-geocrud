Configuration
=============


In your project :

* settings

::

    INSTALLED_APPS = [
        ...
        # apps required by CRUD
        'geostore',  # store geographic data
        'template_model',  # store template in model
        'template_engines',  # generate odt and docx templates
        'rest_framework',  # if you want to try api HTML interface
        'django_json_widget',  # if you want to use django admin
        'reversion',  # used to store every change on data (run ./manage.py createinitialrevisions first)
        # CRUD app
        'terra_geocrud',
        ...
    ]
    ...
    TEMPLATES = [
        ...
        # if you want to render odt templates
        {'BACKEND': 'template_engines.backends.odt.OdtEngine'},
        # if you want to render docx templates
        {'BACKEND': 'template_engines.backends.docx.DocxEngine'},
    ]

* urls

::

    urlpatterns = [
        ...
        path('api/mapbox-baselayer/', include('mapbox_baselayer.urls')),
        path('api/crud/', include('terra_geocrud.urls')),
        ...
    ]

You can customize default url and namespace by including terra_geocrud.views directly

Run migrations

::

    ./manage.py migrate



- ADMIN :

you can disable and / or customize admin

::
from django.contrib import admin
from geostore.models import Layer, Feature
from mapbox_baselayer.admin import MapBaseLayerAdmin
from mapbox_baselayer.models import MapBaseLayer

from terra_geocrud import admin as geocrud_admin, models

admin.site.register(models.CrudGroupView, geocrud_admin.CrudGroupViewAdmin)
admin.site.register(models.CrudView, geocrud_admin.CrudViewAdmin)
admin.site.register(models.AttachmentCategory, geocrud_admin.AttachmentCategoryAdmin)

# we recommend to activate MapBaseLayerAdmin to manage map base layers
admin.site.register(MapBaseLayer, MapBaseLayerAdmin)

# we recommend to use thes admin for this geostore models
admin.site.register(Layer, geocrud_admin.CrudLayerAdmin)
admin.site.register(Feature, geocrud_admin.CrudFeatureAdmin)



- SETTINGS :

Waiting for settings definition directly in models.

Settings should be overrided  with TERRA_GEOCRUD settings in your project settings file:

::

    ...
    TERRA_GEOCRUD = {
        # default value for map extent. API serialize this for layer extent if there is no features in it (as default)
        'EXTENT': [-90.0, -180.0, 90.0, 180.0],
        # default storage for file stored in json properties. It is recommended to configure a private web storage in your project (as S3Storage -> see django-storages)
        'DATA_FILE_STORAGE_CLASS': 'django.core.files.storage.FileSystemStorage',
        # default mapbox style provided by api if no custom style defined in crud view
        'STYLES': {
            'line': {
                'type': 'line',
                'paint': {
                    'line-color': '#000',
                    'line-width': 3
                }
            },
            'point': {
                'type': 'circle',
                'paint': {
                    'circle-color': '#000',
                    'circle-radius': 8
                }
            },
            'polygon': {
                'type': 'fill',
                'paint': {
                    'fill-color': '#000'
                }
            },
        }
    }
    ...

* If you want to generate map on your template with the geometry of your feature, and/or extra features, you should use
  mbglrenderer.

  Check https://github.com/consbio/mbgl-renderer.

  Change the url in the settings to use your instance of mbglrenderer :

::

    MBGLRENDERER_URL = 'http://mbglrenderer'
