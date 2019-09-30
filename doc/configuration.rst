Configuration
=============


In your project :

* settings

::

    INSTALLED_APPS = [
        ...
        # apps required by CRUD
        'geostore',
        'template_model',
        'template_engines',
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
        path('', include('terra_geocrud.urls', namespace='terra_geocrud')),
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
        'EXTENT': [[-90.0, -180.0], [90.0, 180.0]],  # default value for map extent. API serialize this for layer extent if there is no features in it (as default)

    }
    ...
