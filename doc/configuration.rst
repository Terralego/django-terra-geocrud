Configuration
=============


In your project :

* settings

::

    INSTALLED_APPS = [
        ...
        # apps required by CRUD
        'terracommon.terra',
        'template_model',
        # CRUD app
        'terra_crud',
        ...
    ]

* urls

::

    urlpatterns = [
        ...
        path('', include('terra_crud.urls', namespace='terra_crud')),
        ...
    ]

You can customize default url and namespace by including terra_crud.views directly

Run migrations

::

    ./manage.py migrate



- ADMIN :

you can disable and / or customize admin


- SETTINGS :

Waiting for settings definition directly in models.

Settings should be overrided  with TERRA_CRUD settings in your project settings file:

::

    ...
    TERRA_CRUD = {}
    ...

Some keys are available from now :

    TODO: implement base layers for crud here
