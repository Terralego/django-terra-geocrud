import io
import json
import os
import zipfile

from django.core.files import File
from django.contrib.gis.geos import Point
from django.test import TestCase
from geostore.models import Layer, Feature
from template_engines.backends.docx import DocxEngine
from template_model.models import Template

from ..utils import TemplateCacheFile
from .settings import (DOCX_PLAN_DE_GESTION, FEATURE_PROPERTIES, LAYER_COMPOSANTES_SCHEMA,
                       SNAPSHOT_PLAN_DE_GESTION)


class TemplateCacheFileTestCase(TestCase):

    def setUp(self):
        self.layer = Layer.objects.create(
            name='composantes',
            schema=json.load(open(LAYER_COMPOSANTES_SCHEMA)),
            geom_type=1,
        )
        self.feature = Feature.objects.create(
            layer=self.layer,
            geom=Point(x=-0.246322800072846, y=44.5562461167907),
            properties=json.load(open(FEATURE_PROPERTIES)),
        )
        self.template = Template.objects.create(
            name='Template',
            template_file=File(open(DOCX_PLAN_DE_GESTION, 'rb')),
        )
        self.template_cache_file = TemplateCacheFile(self.template, self.feature)

    def test_extension(self):
        self.assertEqual(self.template_cache_file.extension, '.docx')

    def test_name(self):
        self.assertEqual(
            self.template_cache_file.name,
            '{}_{}'.format(self.template.name, self.feature.identifier)
        )

    def test_filename(self):
        self.assertEqual(
            self.template_cache_file.filename,
            os.path.join(
                self.template_cache_file.root_directory,
                '{}{}'.format(self.template_cache_file.name, self.template_cache_file.extension)
            )
        )

    def test_is_outdated(self):
        self.assertTrue(self.template_cache_file.is_outdated)
        self.template_cache_file.set(b'Hello world!')
        self.assertFalse(self.template_cache_file.is_outdated)
        self.template.name = 'Wow'
        self.template.save()
        self.assertTrue(self.template_cache_file.is_outdated)

    def test_get_before_set(self):
        self.assertTrue(self.template_cache_file.get() is None)

    def test_works(self):
        filled_template = DocxEngine({
            'NAME': 'docx',
            'DIRS': [],
            'APP_DIRS': False,
            'OPTIONS': []
        }).get_template(self.template.template_file.name)
        self.template_cache_file.set(filled_template.render(context={'object': self.feature}))
        self.assertTrue(
            os.path.isfile(os.path.join(
                self.template_cache_file.root_directory,
                '{}_updated_at'.format(self.template_cache_file.name)
            )))
        self.assertTrue(os.path.isfile(self.template_cache_file.filename))
        with open(SNAPSHOT_PLAN_DE_GESTION, 'rb') as reader:
            snapshot = reader.read()
        with open(self.template_cache_file.filename, 'rb') as reader:
            buffer = io.BytesIO(reader.read())
            with zipfile.ZipFile(buffer) as zf:
                self.assertEqual(zf.read(os.path.join('word', 'document.xml')), snapshot)
        buffer = io.BytesIO(self.template_cache_file.get())
        with zipfile.ZipFile(buffer) as zf:
            self.assertEqual(zf.read(os.path.join('word', 'document.xml')), snapshot)

    def test_multiple_get(self):
        filled_template = DocxEngine({
            'NAME': 'docx',
            'DIRS': [],
            'APP_DIRS': False,
            'OPTIONS': []
        }).get_template(self.template.template_file.name)
        self.template_cache_file.set(filled_template.render(context={'object': self.feature}))
        with open(SNAPSHOT_PLAN_DE_GESTION, 'rb') as reader:
            snapshot = reader.read()
        first_get = self.template_cache_file.get()
        buffer = io.BytesIO(first_get)
        with zipfile.ZipFile(buffer) as zf:
            self.assertEqual(zf.read(os.path.join('word', 'document.xml')), snapshot)
        second_get = self.template_cache_file.get()
        self.assertEqual(first_get, second_get)

    def test_get_outdated(self):
        filled_template = DocxEngine({
            'NAME': 'docx',
            'DIRS': [],
            'APP_DIRS': False,
            'OPTIONS': []
        }).get_template(self.template.template_file.name)
        self.template_cache_file.set(filled_template.render(context={'object': self.feature}))
        buffer = io.BytesIO(self.template_cache_file.get())
        with open(SNAPSHOT_PLAN_DE_GESTION, 'rb') as reader:
            snapshot = reader.read()
        with zipfile.ZipFile(buffer) as zf:
            self.assertEqual(zf.read(os.path.join('word', 'document.xml')), snapshot)
        self.template.name = 'Michel'
        self.template.save()
        self.assertTrue(self.template_cache_file.get() is None)

    def tearDown(self):
        try:
            os.remove(self.template.template_file.name)
        except FileNotFoundError:
            pass
        try:
            os.remove(self.template_cache_file.filename)
        except FileNotFoundError:
            pass
        try:
            os.remove(os.path.join(
                self.template_cache_file.root_directory,
                '{}_updated_at'.format(self.template_cache_file.name)))
        except FileNotFoundError:
            pass
