from tempfile import TemporaryDirectory

from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.test.testcases import TestCase
from django.urls import reverse
from rest_framework import status

from geostore.models import Feature
from terra_geocrud.models import PropertyDisplayRendering
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

    def test_render_property_data(self):
        self.feature = Feature.objects.create(layer=self.crud_view.layer,
                                              geom=Point(0, 0, srid=4326),
                                              properties={"age": 10, "name": "jec", "country": "slovenija",
                                                          "logo": "data:image/png;name=toto.png;base64,xxxxxxxxxxxx"})
        # add rendering widget
        PropertyDisplayRendering.objects.create(crud_view=self.crud_view,
                                                property='logo',
                                                widget='terra_geocrud.properties.widgets.DataUrlToImgWidget')
        response = self.client.get(reverse('terra_geocrud:feature-detail',
                                           args=(self.feature.layer_id,
                                                 self.feature.identifier)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_data = response.json()
        self.assertNotEqual(json_data['display_properties']['__default__']['properties']['Logo'],
                            self.feature.properties.get('logo'))
        self.assertTrue(json_data['display_properties']['__default__']['properties']['Logo'].startswith('<img '))


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


class PropertyDisplayRenderingTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()

    def test_property_not_in_layer_schema(self):
        with self.assertRaises(ValidationError):
            prop = PropertyDisplayRendering(
                crud_view=self.crud_view,
                property='UNKNOWN_PROPERTY',
                widget='terra_geocrud.properties.widgets.DataUrlToImgWidgetTestCase'
            )
            prop.clean()
