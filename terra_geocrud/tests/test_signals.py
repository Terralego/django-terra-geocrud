from ..properties.schema import sync_layer_schema
from unittest.mock import patch, PropertyMock

from geostore import GeometryTypes
from geostore.models import Feature, LayerRelation
from geostore.tests.factories import LayerFactory
from django.test import TestCase
from django.contrib.gis.geos import LineString

from terra_geocrud.models import CrudViewProperty
from terra_geocrud.tests.factories import CrudViewFactory


class CalculatedPropertiesTest(TestCase):
    def setUp(self) -> None:
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
        self.feature = Feature.objects.create(
            layer=self.crud_view.layer,
            properties={'name': 'toto'},
            geom=LineString((0, 0), (1, 0))
        )

    def test_signal(self):
        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0})
        self.feature.geom = LineString((0, 0), (10, 0))
        self.feature.save()
        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 10.0})

    def test_signal_function_with_validation_error(self):
        self.prop_length.json_schema['type'] = "string"
        self.prop_length.save()
        sync_layer_schema(self.crud_view)
        self.feature.geom = LineString((0, 0), (10, 0))
        self.feature.save()

        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0})

    @patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock)
    def test_signal_function_with_relation(self, mocked):
        mocked.return_value = True
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

        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})

        distance_rel = LayerRelation.objects.create(
            name='cities',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=crud_view.layer,
            settings={"distance": 100}
        )
        self.feature.save()
        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})

        feature = Feature.objects.create(
            layer=layer,
            properties={},
            geom=LineString((0, 0), (10, 0))
        )

        self.feature.sync_relations(distance_rel.pk)
        self.feature.save()
        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})

        feature.properties = {'name': 'City'}
        feature.save()
        self.feature.sync_relations(distance_rel.pk)
        self.feature.save()
        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0, 'cities': ['City']})
