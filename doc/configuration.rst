Configuration
=============


In your project :

* settings

.. code-block:: python

    INSTALLED_APPS = [
        # basic django apps
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        # apps required by terralego stack
        'django.contrib.gis',
        'django.contrib.postgres',
        'rest_framework_gis',
        'rest_framework_jwt',
        'terra_utils',
        'terra_accounts',

        # apps required by CRUD
        'geostore',  # store geographic data
        'template_model',  # store template in model
        'template_engines',  # generate odt and docx templates
        'rest_framework',  # if you want to try api HTML interface
        'django_json_widget',  # if you want to use django admin
        'sorl.thumbnail', # to generate and manage cached image thumbnails
        'mapbox_baselayer', # store and configure mapbox base layers
        'reversion',  # used to store every change on data (run ./manage.py createinitialrevisions first)

        # optional
        'siteprefs', # set some preferences directly in admin

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

.. code-block:: python

    urlpatterns = [
        ...
        # admin
        path('', admin.site.urls), # some base admin views are available in geocrud.

        # terralego based urls
        path('api/', include('terra_utils.urls')),
        path('api/', include('terra_accounts.urls')),

        # urls required for geocrud
        path('api/mapbox_baselayer/', include('mapbox_baselayer.urls')),
        path('api/crud/', include('terra_geocrud.urls')),
        ...
    ]


Run migrations

.. code-block:: bash

    ./manage.py migrate


- SETTINGS :

Some settings are available in django admin, Geographic Editor Config -> Preferences, if admin has been enabled in your project.

.. code-block:: python

    GEOCRUD_MBGLRENDERER_MAX_ZOOM = 22                         # define zoom level max for point map capture (other based on extent)
    GEOCRUD_MAPBOX_ACCESS_TOKEN = None                         # define token to handle mapbox service
    GEOCRUD_DEFAULT_MAP_CENTER_LAT = 0.0                       # Latitude wgs84 for default empty map center
    GEOCRUD_DEFAULT_MAP_CENTER_LNG = 0.0                       # Longitude wgs84 for default empty map center
    GEOCRUD_DEFAULT_MAP_CENTER_ZOOM = 2                        # Zoom level for default empty map
    GEOCRUD_DEFAULT_MAP_MAX_ZOOM = 18                          # Max zoom level for maps
    GEOCRUD_DEFAULT_MAP_MIN_ZOOM = 3                           # Min zoom level for maps
    GEOCRUD_MAP_EXTENT_SW_LAT = -90.0                          # SW latitude wgs84 for empty map extent
    GEOCRUD_MAP_EXTENT_SW_LNG = -180.0                         # SW lonitude wgs84 for empty map extent
    GEOCRUD_MAP_EXTENT_NE_LAT = 90.0                           # NE latitude wgs84 for empty map extent
    GEOCRUD_MAP_EXTENT_NE_LNG = 180.0                          # NE longitude wgs84 for empty map extent
    GEOCRUD_DEFAULT_STYLE_LINE = {"type": "line",              # Default line style used if not defined in crud view
                                  "paint": {
                                      "line-color": "#000",
                                      "line-width": 3
                                  }}
    GEOCRUD_DEFAULT_STYLE_POINT = {"type": "circle",           # Default point style used if not defined in crud view
                                   "paint": {
                                       "circle-color": "#000",
                                       "circle-radius": 8
                                   }}
    GEOCRUD_DEFAULT_STYLE_POLYGON = {"type": "fill",           # Default polygon style used if not defined in crud view
                                     "paint": {
                                         "fill-color": "#000"
                                     }}

These settings should be override in your project settings file only :

* If you want to generate map on your template with the geometry of your feature, and/or extra features, you should use
  mbglrenderer.

  Check https://github.com/consbio/mbgl-renderer.

  Change the url in the settings to use external instance of mbglrenderer :

.. code-block:: python

    GEOCRUD_MBGLRENDERER_URL = 'http://mbglrenderer'


.. code-block:: python

    GEOCRUD_DATA_FILE_STORAGE_CLASS = 'django.core.files.storage.FileSystemStorage'

* This settings manage storage class for feature data files. It will be more secure if you choose a custom private storage backend, like s3 with signature
* Configure this with python doted path to your custom storage backend definition.
* -> See django-storages

