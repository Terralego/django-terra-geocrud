from tempfile import TemporaryDirectory

from django.contrib.gis.geos import Point
from django.test import override_settings
from django.test.testcases import TestCase
from geostore.models import Feature

from terra_geocrud.models import AttachmentCategory, feature_attachment_directory_path, \
    feature_picture_directory_path, CrudViewProperty, FeatureAttachment
from terra_geocrud.properties.files import get_storage
from terra_geocrud.tests import factories
from terra_geocrud.tests.factories import CrudViewFactory, FeaturePictureFactory, FeatureAttachmentFactory
from .. import models
from ..properties.schema import sync_layer_schema, sync_ui_schema

storage = get_storage()


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
        self.mixin = FeatureAttachment(category=self.category, legend='test')

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


class CrudViewPropertyTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        self.prop_1 = CrudViewProperty.objects.create(view=self.crud_view, key="name",
                                                      json_schema={'type': "string", "title": "Name"},
                                                      ui_schema={'title': 'Real name'})
        self.prop_2 = CrudViewProperty.objects.create(view=self.crud_view, key="age",
                                                      json_schema={'type': "integer", "title": "Age"})
        self.prop_3 = CrudViewProperty.objects.create(view=self.crud_view, key="country",
                                                      json_schema={'type': "string"})

    def test_str(self):
        self.assertEqual(str(self.prop_1), f"{self.prop_1.title} ({self.prop_1.key})")

    def test_title_defined_in_uischema(self):
        """ Title defined in ui schema sould be considered at first """
        self.assertEqual(self.prop_1.title, self.prop_1.ui_schema.get('title'))

    def test_title_define_in_jsonschema(self):
        """ Title defined in json schema sould be considered if not defined in ui schema """
        self.assertEqual(self.prop_2.title, self.prop_2.json_schema.get('title'))

    def test_title_not_defined(self):
        """ Title not defined in json or ui schema should be key capitalized """
        self.assertEqual(self.prop_3.title, self.prop_3.key.capitalize())


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class FeaturePictureTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        self.feature = Feature.objects.create(layer=self.crud_view.layer,
                                              geom='POINT(0 0)')
        self.pic = FeaturePictureFactory(feature=self.feature)

    def test_image_and_thumbnail_deleted_after_deletion(self):
        # image exists in storage
        self.assertTrue(storage.exists(self.pic.image.name))
        # generate thumbnail
        thumbnail = self.pic.thumbnail
        self.assertTrue(storage.exists(thumbnail.name))
        # delete image
        self.pic.delete()
        self.assertFalse(storage.exists(self.pic.image.name))
        self.assertFalse(storage.exists(thumbnail.name))


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class FeatureAttachmentTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        self.feature = Feature.objects.create(layer=self.crud_view.layer,
                                              geom='POINT(0 0)')
        self.attachment = FeatureAttachmentFactory(feature=self.feature)

    def test_file_deleted_after_feature_deletion(self):
        # file exists in storage
        self.assertTrue(storage.exists(self.attachment.file.name))
        # delete attachment
        self.attachment.delete()
        # file not in storage anymore
        self.assertFalse(storage.exists(self.attachment.file.name))
