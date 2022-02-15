CHANGELOG
=========

1.0.24         (2022-02-15)
---------------------------

* Add deletion signal delete properties pictures and thumbnails

1.0.23   	   (2022-02-11)
---------------------------

* Add relation layer in vector tiles

1.0.22	      (2021-10-19)
---------------------------

* Add layer pk in crud/settings map_layers (relation and extra_geom)

1.0.21		   (2021-10-18)
---------------------------

* Rename crud/settings 'source' to 'view_source'

1.0.20         (2020-10-14)
----------------------------

* Change crud/settings generation so that '.menu[].crud_views[].map_layers' now includes related layer. A source attribute has been added to distinguish layers from "relations" and layers from "extra_geometry"

1.0.19          (2021-09-30)
----------------------------

* Fix concurrency issue when synchronizing relations between Features. This issue was causing data loss when a user tried to edit a feature properties while a celery task was also updating those properties.


1.0.18          (2021-09-20)
----------------------------

* Remove duplicates tasks signals
* Add feature properties list order


1.0.17          (2021-09-14)
----------------------------

* Improve performance signals relations


1.0.16          (2021-07-05)
----------------------------

* Add migration validation function_path
* Remove image generated from property before generate a new one


1.0.15          (2021-04-30)
----------------------------

* Change relations : add geojson informations, label, empty


1.0.14          (2021-04-16)
----------------------------

* Use defined pictograms in multi values in display properties


1.0.13          (2021-04-01)
----------------------------

* Fix task modification of destination and origin props


1.0.12          (2021-03-31)
----------------------------

* Use defined pictograms in values in display properties
* Update calculated properties only if feature still exists (async)


1.0.11          (2021-03-12)
----------------------------

* Fix signals calculated properties, with save of layer relation, save and delete of destinations


1.0.10          (2021-03-04)
----------------------------

* Add routing informations on each features
* Add calculated properties


1.0.9           (2021-02-18)
----------------------------

* Fix routing queryset get all layers not only with crud_view


1.0.8           (2021-02-16)
----------------------------

* Update french translations


1.0.7           (2021-02-12)
----------------------------

* Fix relation with crud views
* Add admin relations


1.0.6           (2021-02-11)
----------------------------

* Add field editable on crud view properties


1.0.5           (2021-01-22)
----------------------------

* Fix constraints different crudviews for routing settings


1.0.4           (2021-01-22)
----------------------------

* Add routing settings for each crudview


1.0.3           (2020-12-10)
----------------------------

* Remove compatibility with terra-accounts <= 1.0


1.0.2           (2020-12-10)
----------------------------

* Provide right url for async exports


1.0.1           (2020-12-04)
----------------------------

* Compatibility with terra-accounts >= 1.0 and terra-settings >= 1.0
* Compatibility with django-mapbox-baselayers last version


1.0.0           (2020-10-28)
----------------------------

FIRST real release

* Allow to define which property should be included in vector tile
* Fix cases when layer has not yet schema definition
* Allow to define custom list choicers for poperties (enums) associated with pictograms.


0.3.49          (2020-10-16)
----------------------------

* Support new "image_base64_from_url" tag to get base64 encoded image from url.


0.3.48          (2020-10-14)
----------------------------

* Fix case where pdf is not identified


0.3.47          (2020-09-15)
----------------------------

* Improve admin

0.3.46          (2020-09-15)
----------------------------

* use django-admin-thumbnails to show and manage pictograms in django admin
* use standard header access in http response to avoid deprecation in future django 3.2

0.3.45          (2020-09-11)
----------------------------

* Fix deprecation warnings in django 3.1

0.3.44          (2020-09-09)
----------------------------

* Support Django 3.1
* Terra Accounts User Model is not required anymore
* Dont clean features values when property is deleted. (Need to clean with admin crud view action)

0.3.43          (2020-05-27)
----------------------------

* Fix case with date format

0.3.42          (2020-05-27)
----------------------------

* Format date in display values
* Fix default cases when layer has no schema

0.3.41          (2020-05-26)
----------------------------

* Fix mandatory field in crud view admin
* Fix feature cleaning method

0.3.40          (2020-05-25)
----------------------------

* Gdal supported file format to import data in admin

0.3.39          (2020-05-15)
----------------------------

* Update translations
* Fix deprecation and resource warnings
* Delete thumbnail to image deletion
* Delete media files to image deletion


0.3.38.1        (2020-04-24)
----------------------------

* fix translations
* fix feature properties cleaning


0.3.38          (2020-04-23)
----------------------------

* validate json schema properties
* Disable property value affectation at creation


0.3.37          (2020-04-20)
----------------------------

* improve thumbnail generation
* change api default order for attachments and pictures


0.3.36          (2020-04-17)
----------------------------

* Helper to sort elements in django admin


0.3.35          (2020-04-17)
----------------------------

* Fix way to generate templates
* Add local server time to generated files from templates
* Improve settings with supported image formats and max upload file size in bytes
* Now all properties are managed directly in Crud View admin
* Feature detail api endpoint improved


0.3.34          (2020-03-20)
----------------------------
## Bug fixes

* Fix image url in array
* Try to fix some thumbnail generation

## Features

* Add all geometries description in feature detail serializer
* Change generated document name with feature title
* Custom serializer for feature extra geometries
* Fix old serializer feature properties
* Manage plural names for crud views

## Deprecate

* feature serializer new_display_properties became display_properties
* extra_geometries is no longer available
* Widget for data rendering is no longer available


0.3.33          (2020-02-14)
----------------------------

* BREAKING CHANGES : new way to store path in storage
* Fix image generation from data stored image
* New template tag to handle image from data-url stored image
* Fix bug in admin

0.3.32          (2020-02-06)
----------------------------

* Back to django 3.0 compatibility
* New serializer detail to provide features properties informations and data


0.3.31          (2020-01-29)
----------------------------

* Fix compatibility with geostore 0.3.16


0.3.30          (2020-01-27)
----------------------------

* back from django 2.2 maxi. Wait for sorl-thumbnail 12.6.0


0.3.29          (2020-01-27)
----------------------------

* Support Django 3.0
* Compatibility with geostore 0.3.16


0.3.28          (2019-12-17)
----------------------------

* Django Rest Framework 3.11 compatibility
* Python 3.8 compatibility


0.3.27          (2019-12-11)
----------------------------

* Fake data-url content to decrease feature json property size


0.3.26          (2019-12-05)
----------------------------

* add extra geometries identifiers in feature detail endpoint


0.3.25          (2019-12-04)
----------------------------

* HotFix custom styles management


0.3.24          (2019-12-04)
----------------------------

* add crud view property to describe available layers for layer / feature (extra) geometries


0.3.23          (2019-12-03)
----------------------------

* fix settings with only MAX_ZOOM for map style
* Add map_image_url_loader tag  allowing to add map with style, extra_features
* add property to generated mapbox style


0.3.22          (2019-11-13)
----------------------------

* ability to hide ungrouped views in config menu

0.3.21          (2019-11-04)
----------------------------

* Add default widget to render array object as table


0.3.20          (2019-10-21)
----------------------------

* Picture and attachments are not grouped anymore


0.3.19          (2019-10-21)
----------------------------

* Picture and attachments are now behind feature
* Split public / private settings


0.3.18          (2019-10-18)
----------------------------

* Improve integration in terralego settings system
* Manage attachments and pictures to features


0.3.17          (2019-10-17)
----------------------------

News:

* Admin is not longer activated by default. Please configure in your project


0.3.16          (2019-10-15)
----------------------------

Fixes:

* fix admin with custom geostore admin

News:

* Add french translations

0.3.15          (2019-10-14)
----------------------------

* fix missing permissions


0.3.14          (2019-10-14)
----------------------------

* Fix default extent as simple array
* Use django-reversion to keep changes in admin
* Add functionnal permissions (used only in frontend for the moment)


0.3.13          (2019-10-11)
----------------------------

Fixes

* map_style is now empty and not null in case of undefined geometry layer
* extent for layer with no features


0.3.12          (2019-10-11)
----------------------------

Update

* Optimize widget rendering


0.3.11          (2019-10-10)
----------------------------

Update

* Optimize data file storage


0.3.10          (2019-10-09)
----------------------------

News

* Store and serve data file through a customizable django storage (FileSystem / Public by default)

Fixes

* Fix dict iteration in feature creation


0.3.9           (2019-10-09)
----------------------------

Fixes

* Fix feature creation with grouped properties

News

* Add Date format property render widget.


0.3.8           (2019-10-08)
----------------------------

News

* Add json editor in django admin
* Define wich property is used to display feature title

Update

* Generated template default file name.


0.3.7           (2019-10-07)
----------------------------

Fixes

* ui-order and ui-widget to ui:order and ui:widget


0.3.6           (2019-10-07)
----------------------------

Fixes

* fix ui-order for groups in ui-schema


0.3.5           (2019-10-07)
----------------------------

Feature

* ability to define custom widgets for feature property rendering in crud view


0.3.4           (2019-10-04)
----------------------------

Fixes

* feature default list fix


0.3.3      (2019-10-04)
-----------------------

Feature

* ui-schema fixed in api with group defined
* feature_list_properties are now in object instead of single array element


0.3.1      (2019-09-30)
-----------------------

Features

* Ability to groups layers properties in form schema and data display
* New layer/<layer/features endpoint that provide custom data. Usage of old geostore endpoint will be deprecated.
* Improve CrudView serializer to provide required frontend data, and give frontend urls to follow.

0.3.0      (2019-09-24)
-----------------------

Breaking changes
* app renamed from terra_crud to terra_geocrud

Update

* requirements (`django-template-model>=1.0.1` and `django-template-engines>=1.2.9`)

0.1.4      (2019-11-13)
-----------------------

Breaking change

* replace template rendering url parameter from {pk} to {id}


0.1.3      (2019-11-13)
-----------------------

Fix

* Unquote template rendered url in API


0.1.2      (2019-11-13)
-----------------------

Update

* Default template generation with template original name


0.1.1      (2019-11-11)
-----------------------

Fixes

* Compatibility with django external storage


0.1.0      (2019-11-11)
-----------------------

Fixes

* Fixup rendering issue


0.0.1.dev3 (2019-09-10)
-----------------------

Features

* Manage template models for each crud view


Breaking changes

* Require django-template-model, django-template-engine and extra configuration (see documentation)


0.0.1.dev2 (2019-09-02)
-----------------------

Update

* Require terra-common v0.0.2

Fixes

* Delete unused null=True

0.0.1.dev1 (2019-08-29)
-----------------------

Add features

* Set template M2M

0.0.1.dev0 (2019-08-28)
-----------------------

First release
