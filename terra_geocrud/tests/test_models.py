from tempfile import TemporaryDirectory

from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.test.testcases import TestCase
from django.urls import reverse
from rest_framework import status
from terra_geocrud.tests.factories import CrudViewFactory, FeaturePictureFactory

from geostore.models import Feature, LayerSchemaProperty, ArrayObjectProperty
from geostore.tests.factories import LayerFactory
from terra_geocrud.models import PropertyDisplayRendering, AttachmentCategory, AttachmentMixin, \
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
        self.other_layer = LayerFactory()
        self.crud_view = factories.CrudViewFactory()
        LayerSchemaProperty.objects.create(required=False, prop_type="string", title="Logo",
                                           layer=self.crud_view.layer)
        self.other_schema_property = LayerSchemaProperty.objects.create(required=False,
                                                                        prop_type="string",
                                                                        title="Country",
                                                                        layer=self.other_layer)

    def test_clean_default_list_properties(self):
        with self.assertRaises(ValidationError):
            self.crud_view.default_list_properties.add(self.other_schema_property)
            self.crud_view.clean()

    def test_clean_feature_title_property(self):
        with self.assertRaises(ValidationError):
            self.crud_view.feature_title_property = self.other_schema_property
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
        response = self.client.get(reverse('feature-detail',
                                           args=(self.feature.layer_id,
                                                 self.feature.identifier)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_data = response.json()
        self.assertNotEqual(json_data['display_properties']['__default__']['properties']['Logo'],
                            self.feature.properties.get('logo'))
        self.assertTrue(json_data['display_properties']['__default__']['properties']['Logo'].startswith('<img '))

    def test_complex_ui_schema(self):
        layer = LayerFactory()
        layer_schema = LayerSchemaProperty.objects.create(required=True, prop_type="string", title="Name", layer=layer)
        layer_schema_2 = LayerSchemaProperty.objects.create(required=False, prop_type="integer", title="Age",
                                                            layer=layer)
        layer_schema_array = LayerSchemaProperty.objects.create(required=False, prop_type="array",
                                                                array_type="object", title="Other",
                                                                layer=layer)
        array_schema_1 = ArrayObjectProperty.objects.create(prop_type="string", title="column",
                                                            array_property=layer_schema_array)
        array_schema_2 = ArrayObjectProperty.objects.create(prop_type="int", title="column2",
                                                            array_property=layer_schema_array)
        models.UISchemaProperty.objects.create(crud_view=self.crud_view, layer_schema=layer_schema,
                                               schema={'ui:widget': 'textarea'}, order=1)
        models.UISchemaProperty.objects.create(crud_view=self.crud_view, layer_schema=layer_schema_2, order=2)
        ui_schema_with_array = models.UISchemaProperty.objects.create(crud_view=self.crud_view,
                                                                      layer_schema=layer_schema_array)
        models.UIArraySchemaProperty.objects.create(ui_schema_property=ui_schema_with_array,
                                                    array_layer_schema=array_schema_1, order=1)
        models.UIArraySchemaProperty.objects.create(ui_schema_property=ui_schema_with_array,
                                                    array_layer_schema=array_schema_2,
                                                    schema={'ui:widget': 'textarea'})
        self.assertEqual({'other': {'items': {'column2': {'ui:widget': 'textarea'}, 'ui:order': ['column']}},
                          'name': {'ui:widget': 'textarea'},
                          'ui:order': ['name', 'age', '*']},
                         self.crud_view.generated_ui_schema)


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


class UISchemaAndUIArraySchemaPropertyTestCase(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory(name="Foo")
        layer = LayerFactory()
        self.ui_schema = models.UISchemaProperty()
        layer_schema_array = LayerSchemaProperty.objects.create(required=False, prop_type="array",
                                                                array_type="object", title="Other",
                                                                layer=layer)
        array_schema_1 = ArrayObjectProperty.objects.create(prop_type="string", title="column",
                                                            array_property=layer_schema_array)
        self.ui_schema = models.UISchemaProperty.objects.create(crud_view=self.crud_view,
                                                                layer_schema=layer_schema_array)
        self.ui_array_schema = models.UIArraySchemaProperty.objects.create(ui_schema_property=self.ui_schema,
                                                                           array_layer_schema=array_schema_1)

    def test_str_schema(self):
        self.assertEqual('Foo: other (array)', str(self.ui_schema))

    def test_str_array_schema(self):
        self.assertEqual('Foo: other (array): column (string)', str(self.ui_array_schema))
