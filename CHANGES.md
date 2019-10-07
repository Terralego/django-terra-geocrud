=========
CHANGELOG
=========

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
