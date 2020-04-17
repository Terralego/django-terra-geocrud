=========
CHANGELOG
=========

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
