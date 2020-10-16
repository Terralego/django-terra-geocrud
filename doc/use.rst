Example of use
==============

- django-terra-gecorud provide its own settings url

/api/crud/settings/


- There are 4 endpoint in GEOCRUD API:


::

    settings/                     -> get ordered menu with views classified by group or not, and basic map settings
    groups/                       -> manage groups of CRUD views
    views/                        -> manage CRUD views (a view creation create its associated layer)

- A command is available to create default views for each existing layer

::

    ./manage.py create_default_crud_views

- START GUIDE


- First, you need to create crud views for your geostore layers with the command or the admin.
- These views can be grouped, and will be listed by the frontend api
- Then, you can customize default layer-schema by providing your own property groups, which will groups properties as json schema nested objects.


## ADMIN

* Some classes are provided to help you to manage Crud views / groups / layers and feature through django admin.
* You need to register your wanted ModelAdmin in your project


## TEMPLATES

* Check https://github.com/Terralego/django-template-engines to create your own template.
* In addition to the ODTEngine and DocXEngine, for odt only, you can add maps of layers with features and extra_features.
  Use :

    ::

        {% load map_tags %}
        {# in odt files #}
        {% map_image_url_loader feature_included=True extra_features="Extra_feature_slug,Extra_feature_2_slug"
         base_layer="mapbox_baselayer_slug" %}
         {# in pdf files #}
        {% image_base64_from_url feature_included=True extra_features="Extra_feature_slug,Extra_feature_2_slug"
         base_layer="mapbox_baselayer_slug" %}
         image_base64_from_url

  You can use the other tags : width, height, anchor.
