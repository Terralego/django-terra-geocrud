from tempfile import TemporaryDirectory

from django.contrib.gis.geos import Point
from django.test import override_settings
from django.test.testcases import TestCase
from terra_geocrud.tests.factories import CrudViewFactory, FeaturePictureFactory

from geostore.models import Feature
from terra_geocrud.models import AttachmentCategory, AttachmentMixin, \
    feature_attachment_directory_path, feature_picture_directory_path, CrudViewProperty
from terra_geocrud.tests import factories
from .. import models
from ..properties.schema import sync_layer_schema, sync_ui_schema


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


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class FeaturePropertyDisplayGroupTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        self.group_1 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test')
        self.group_2 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test2')
        CrudViewProperty.objects.create(view=self.crud_view, key="name",
                                        group=self.group_2,
                                        required=True,
                                        json_schema={'type': "string", "title": "Name"},
                                        ui_schema={'ui:widget': 'textarea'})
        CrudViewProperty.objects.create(view=self.crud_view, key="age",
                                        group=self.group_1,
                                        json_schema={'type': "integer", "title": "Age"})
        CrudViewProperty.objects.create(view=self.crud_view, key="country",
                                        json_schema={'type': "string", "title": "Country"})
        self.feature = Feature.objects.create(geom=Point(0, 0, srid=4326),
                                              properties={"age": 10, "name": "jec", "country": "slovenija"},
                                              layer=self.crud_view.layer)
        self.template = factories.TemplateDocxFactory()
        self.crud_view.templates.add(self.template)
        sync_layer_schema(self.crud_view)
        sync_ui_schema(self.crud_view)

    def test_str(self):
        self.assertEqual(str(self.group_1), self.group_1.label)

    def test_form_schema(self):
        self.assertDictEqual(self.group_1.form_schema,
                             {'properties': {'age': {'title': 'Age', 'type': 'integer'}},
                              'required': [],
                              'title': 'test',
                              'type': 'object'
                              })
        self.assertDictEqual(self.group_2.form_schema,
                             {'properties': {'name': {'title': 'Name', 'type': 'string'}},
                              'required': ['name'],
                              'title': 'test2',
                              'type': 'object'
                              })
        self.maxDiff = None
        self.assertDictEqual(self.crud_view.grouped_form_schema, {
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
