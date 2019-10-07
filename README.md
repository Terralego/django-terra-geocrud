[![Build Status](https://travis-ci.org/Terralego/django-terra-geocrud.svg?branch=master)](https://travis-ci.org/Terralego/django-terra-geocrud)
[![codecov](https://codecov.io/gh/Terralego/django-terra-geocrud/branch/master/graph/badge.svg)](https://codecov.io/gh/Terralego/django-terra-geocrud)
[![Maintainability](https://api.codeclimate.com/v1/badges/633c620b6dcfc0e18df2/maintainability)](https://codeclimate.com/github/Terralego/django-terra-geocrud/maintainability)

https://django-terra-geocrud.readthedocs.io/

CRUD views definition for django-geostore in terra apps

* Customize Left menu from gesotore layers
* Customized endpoints to manage layers and features
* Group properties, order them, define layout and widgets to render them.


## Requirements

* django-geostore >= 0.3.1
* django-template-models
* django-template-engines

## DEVELOPMENT

### with docker :
```bash
$ docker-compose build
$ docker-compose up
....
$ docker-compose run web /code/venv/bin/python3.7 ./manage.py shell
$ docker-compose run web coverage run ./manage.py test
```

### with pip :
```bash
$ python3.7 -m venv venv
$ source activate venv/bin/activate
pip install -e .[dev]
```
