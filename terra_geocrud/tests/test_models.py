from tempfile import TemporaryDirectory

from django.contrib.gis.geos import Point
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


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class FeaturePropertyDisplayGroupTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        self.group_1 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test')

    def test_str(self):
        self.assertEqual(str(self.group_1), self.group_1.label)


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
