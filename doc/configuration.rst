Configuration
=============


In your project :

* settings

::

    INSTALLED_APPS = [
        ...
        'terracommon.terra',
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



ADMIN

you can disable and / or customize admin
