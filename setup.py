#!/usr/bin/env python

import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(HERE, 'README.md')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.md')).read()

tests_require = [
    'factory-boy',
    'flake8',
    'coverage',
]

setup(
    name='django-terra-geocrud',
    version=open(os.path.join(HERE, 'terra_geocrud', 'VERSION.md')).read().strip(),
    include_package_data=True,
    author="Makina Corpus",
    author_email="terralego-pypi@makina-corpus.com",
    description='Geographic CRUD for django-geostore',
    long_description=README + '\n\n' + CHANGES,
    description_content_type="text/markdown",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url='https://github.com/Terralego/django-terra-geocrud.git',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
    ],
    install_requires=[
        'django>=2.2,<3.0',  # 3.0 blocked by solr-thumbnail and django-restframework-gis
        'django-reversion>=3.0.4',
        'django-template-model>=1.0.1',
        'django-template-engines>=1.2.24',
        'django-mapbox-baselayer>=0.0.3',
        'django-geostore>=0.3.12',
        'django-terra-accounts>=0.3.7.1',
        'djangorestframework>=3.10',
        'djangorestframework-gis>=0.14',
        'requests',
        'django-json-widget>=0.2.0',
        'pillow',
        'sorl-thumbnail',
    ],
    tests_require=tests_require,
    extras_require={
        'dev': tests_require + [
            'django-debug-toolbar',
        ]
    }
)
