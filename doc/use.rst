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

- DOCX and ODT templates can be uploaded. You can use the same tags as in the Django Html templates. If you want to insert the image of a map, add the following code at the top of your template:

::

    {% load docx_image_loader %}

Then, each time you want to insert the image use:

::

    {% docx_image_loader map %}
