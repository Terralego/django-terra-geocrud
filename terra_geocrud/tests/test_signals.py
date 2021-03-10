from ..properties.schema import sync_layer_schema
from unittest.mock import patch, PropertyMock

from geostore import GeometryTypes
from geostore.models import Feature, LayerRelation
from geostore.tests.factories import LayerFactory
from django.test import TestCase

from django.contrib.gis.geos import LineString

from terra_geocrud.models import CrudViewProperty
from terra_geocrud.tests.factories import CrudViewFactory


@patch('terra_geocrud.signals.execute_async_func')
@patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock)
class CalculatedPropertiesTest(TestCase):
    def setUp(self):

        layer = LayerFactory.create(geom_type=GeometryTypes.LineString,
                                    schema={"type": "object",
                                            "required": ["name", ],
                                            "properties": {"name": {"type": "string", "title": "Name"}}
                                            })
        self.crud_view = CrudViewFactory(layer=layer)
        self.prop_length = CrudViewProperty.objects.create(
            view=self.crud_view, key="length",
            editable=False,
            json_schema={'type': "integer", "title": "Length"},
            function_path='test_terra_geocrud.functions_test.get_length'
        )
        self.prop_name = CrudViewProperty.objects.create(
            view=self.crud_view, key="name",
            editable=True,
            json_schema={'type': "string", "title": "Name"}
        )
        sync_layer_schema(self.crud_view)
        with patch('terra_geocrud.signals.execute_async_func') as mocked_async:
            self.add_side_effect_async(mocked_async)
            with patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock) as mocked:
                mocked.return_value = True
                self.feature = Feature.objects.create(
                    layer=self.crud_view.layer,
                    properties={'name': 'toto'},
                    geom=LineString((0, 0), (1, 0))
                )

    def add_side_effect_async(self, mocked):
        def side_effect_async(async_func, args=()):
            async_func(*args)
        mocked.side_effect = side_effect_async

    def test_signal(self, property_mocked, async_mocked):
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        feature = Feature.objects.get(pk=self.feature.pk)
        self.assertEqual(feature.properties, {'name': 'toto', 'length': 1.0})
        self.feature.geom = LineString((0, 0), (10, 0))
        self.feature.save()
        feature = Feature.objects.get(pk=self.feature.pk)
        self.assertEqual(feature.properties, {'name': 'toto', 'length': 10.0})

    def test_signal_function_with_validation_error(self, property_mocked, async_mocked):
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        self.prop_length.json_schema['type'] = "string"
        self.prop_length.save()
        sync_layer_schema(self.crud_view)

        feature = Feature.objects.get(pk=self.feature.pk)
        feature.geom = LineString((0, 0), (10, 0))
        feature.save()

        feature = Feature.objects.get(pk=self.feature.pk)

        self.assertEqual(feature.properties, {'name': 'toto', 'length': 1.0})

    def test_signal_function_with_relation(self, property_mocked, async_mocked):
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        layer = LayerFactory.create(geom_type=GeometryTypes.LineString,
                                    schema={"type": "object",
                                            "required": ["name", ],
                                            "properties": {"name": {"type": "string", "title": "Name"}}
                                            })
        crud_view = CrudViewFactory.create(layer=layer)
        self.prop_relation = CrudViewProperty.objects.create(
            view=self.crud_view, key="cities",
            editable=False,
            json_schema={'type': "array", "items": {"type": "string"}},
            function_path='test_terra_geocrud.functions_test.get_cities'
        )

        sync_layer_schema(self.crud_view)
        sync_layer_schema(crud_view)

        self.feature.save()

        feature = Feature.objects.get(pk=self.feature.pk)
        self.assertEqual(feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})
        distance_rel = LayerRelation.objects.create(
            name='cities',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=crud_view.layer,
            settings={"distance": 100}
        )
        self.feature.save()

        feature = Feature.objects.get(pk=self.feature.pk)
        self.assertEqual(feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})

        feature_intersect = Feature.objects.create(
            layer=layer,
            properties={},
            geom=LineString((0, 0), (10, 0))
        )

        self.feature.sync_relations(distance_rel.pk)
        self.feature.save()
        feature = Feature.objects.get(pk=self.feature.pk)
        self.assertEqual(feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})

        feature_intersect.properties = {'name': 'City'}
        feature_intersect.save()
        self.feature.sync_relations(distance_rel.pk)
        self.feature.save()
        feature = Feature.objects.get(pk=self.feature.pk)
        self.assertEqual(feature.properties, {'name': 'toto', 'length': 1.0, 'cities': ['City']})
