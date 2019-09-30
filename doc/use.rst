Example of use
==============

- By default, api endpoints are available under

::

    /api/crud/

- There are 4 endpoint:

::

    /api/crud/groups/                       -> manage groups of CRUD views
    /api/crud/views/                        -> manage CRUD views (a view creation create its associated layer)
    /api/crud/settings/                     -> get ordered menu with views classified by group or not, and basic map settings
    /api/crud/template/<template_pk>/render/<pk>/ -> fill a template with a feature

- A command is available to create default views for each existing layer

::

    ./manage.py create_default_crud_views

- START GUIDE


- First, you need to create crud views for your geostore layers with the command or the admin.
- These views can be grouped, and will be listed by the frontend api
- Then, you can customize default layer-schema by providing your own property groups, which will groups properties as json schema nested objects.


## ADMIN

* access to /admin/terra_geocrud/
