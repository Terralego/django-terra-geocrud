from tempfile import TemporaryDirectory

from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.test.testcases import TestCase
from terra_geocrud.tests.factories import CrudViewFactory, FeaturePictureFactory

from geostore.models import Feature
from terra_geocrud.models import AttachmentCategory, AttachmentMixin, \
    feature_attachment_directory_path, feature_picture_directory_path
from terra_geocrud.tests import factories
from .. import models


class CrudModelMixinTestCase(TestCase):
    def test_str_method(self):
        class MyTestModel(models.CrudModelMixin):
            name = 'test'

        a = MyTestModel()
        self.assertEqual(a.name, str(a))


class CrudViewTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory(
            layer__schema={
                "type": "object",
                "required": ["name", ],
                "properties": {
                    "name": {
                        'type': "string",
                        "title": "Name"
                    },
                    "logo": {
                        'type': "string",
                        "title": "Logo",
                        "format": "data-url"
                    },
                    "age": {
                        'type': "integer",
                        "title": "Age",
                    },
                    "country": {
                        'type': "string",
                        "title": "Country"
                    },
                }
            }
        )

    def test_clean_default_list_properties(self):
        with self.assertRaises(ValidationError):
            self.crud_view.default_list_properties.append('toto')
            self.crud_view.clean()

    def test_clean_feature_title_property(self):
        with self.assertRaises(ValidationError):
            self.crud_view.feature_title_property = 'toto'
            self.crud_view.clean()


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class FeaturePropertyDisplayGroupTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        self.group_1 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test',
                                                                         properties=['age'])
        self.group_2 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test2',
                                                                         properties=['name'])
        self.feature = Feature.objects.create(geom=Point(0, 0, srid=4326),
                                              properties={"age": 10, "name": "jec", "country": "slovenija"},
                                              layer=self.crud_view.layer)
        self.template = factories.TemplateDocxFactory()
        self.crud_view.templates.add(self.template)

    def test_str(self):
        self.assertEqual(str(self.group_1), self.group_1.label)

    def test_form_schema(self):
        self.assertDictEqual(self.group_1.form_schema,
                             {'properties': {'age': {'title': 'Age', 'type': 'integer'}},
                              'required': [],
                              'title': 'test',
                              'type': 'object'
                              }
                             )
        self.assertDictEqual(self.group_2.form_schema,
                             {'properties': {'name': {'title': 'Name', 'type': 'string'}},
                              'required': ['name'],
                              'title': 'test2',
                              'type': 'object'
                              })
        self.maxDiff = None
        self.assertDictEqual(self.crud_view.grouped_form_schema, {
            "type": "object",
            "required": [],
            "properties": {
                'country': {
                    'type': 'string',
                    'title': 'Country'
                },
                'test': {
                    'properties': {'age': {'title': 'Age', 'type': 'integer'}},
                    'required': [],
                    'title': 'test',
                    'type': 'object'
                },
                'test2': {
                    'properties': {'name': {'title': 'Name', 'type': 'string'}},
                    'required': ['name'],
                    'title': 'test2',
                    'type': 'object'
                },
            }
        })

    def test_clean(self):
        with self.assertRaises(ValidationError):
            self.group_1.properties.append('toto')
            self.group_1.clean()


class AttachmentCategoryTestCase(TestCase):
    def setUp(self) -> None:
        self.category = AttachmentCategory.objects.create(name='cat test')

    def test_str(self):
        self.assertEqual(self.category.name, str(self.category))


class AttachmentMixinTestCase(TestCase):
    def setUp(self) -> None:
        self.category = AttachmentCategory.objects.create(name='cat test')
        self.mixin = AttachmentMixin(category=self.category, legend='test')

    def test_str(self):
        self.assertEqual(str(self.mixin), 'test - (cat test)')


class AttachmentTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = CrudViewFactory()
        self.feature = Feature.objects.create(
            layer=self.crud_view.layer,
            properties={'name': 'toto'},
            geom=Point(0, 0)
        )
        self.feature_picture = FeaturePictureFactory(feature=self.feature)

    def test_feature_attachment_directory_path(self):
        self.assertEqual(feature_attachment_directory_path(self.feature_picture, 'toto.jpg'),
                         f'terra_geocrud/features/{self.feature.pk}/attachments/toto.jpg')

    def test_feature_picture_directory_path(self):
        self.assertEqual(feature_picture_directory_path(self.feature_picture, 'toto.jpg'),
                         f'terra_geocrud/features/{self.feature.pk}/pictures/toto.jpg')

    def test_picture_thumbnail(self):
        thumbnail = self.feature_picture.thumbnail
        self.assertIsNotNone(thumbnail)
