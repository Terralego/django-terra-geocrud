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
        # some urls in geostore are required by geocrud
        path('api/geostore/', include('geostore.urls')),
        path('api/crud/', include('terra_geocrud.urls')),
        ...
    ]

You can customize default url and namespace by including terra_geocrud.views directly

Run migrations

::

    ./manage.py migrate



- ADMIN :

you can disable and / or customize admin


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