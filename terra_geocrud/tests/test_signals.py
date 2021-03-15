from ..properties.schema import sync_layer_schema
from unittest.mock import patch, PropertyMock

from geostore import GeometryTypes
from geostore.models import Feature, LayerRelation
from geostore.tests.factories import LayerFactory
from django.test import TestCase

from django.contrib.gis.geos import LineString, Polygon

from terra_geocrud.models import CrudViewProperty
from terra_geocrud.tasks import feature_update_relations_destinations, feature_update_relations_origins
from terra_geocrud.tests.factories import CrudViewFactory


class AsyncSideEffect(object):
    def add_side_effect_async(self, mocked):
        def side_effect_async(async_func, args=()):
            async_func(*args)
        mocked.side_effect = side_effect_async


@patch('terra_geocrud.tasks.feature_update_relations_destinations.delay')
@patch('terra_geocrud.signals.execute_async_func')
@patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock)
class CalculatedPropertiesTest(AsyncSideEffect, TestCase):
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
                self.feature_long = Feature.objects.create(
                    layer=self.crud_view.layer,
                    properties={'name': 'tata'},
                    geom=LineString((0, 0), (10, 10))
                )

    def test_signal(self, property_mocked, async_mocked, mock_delay):
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        self.feature.refresh_from_db()
        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0})
        self.feature.geom = LineString((0, 0), (10, 0))
        self.feature.save()
        self.feature.refresh_from_db()

        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 10.0})

    def test_signal_function_with_validation_error(self, property_mocked, async_mocked, mock_delay):
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        self.prop_length.json_schema['type'] = "string"
        self.prop_length.save()
        sync_layer_schema(self.crud_view)

        feature = Feature.objects.get(pk=self.feature.pk)
        feature.geom = LineString((0, 0), (10, 0))
        feature.save()

        self.feature.refresh_from_db()

        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0})

    def test_signal_function_with_relation(self, property_mocked, async_mocked, mock_delay):
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
        self.feature.refresh_from_db()

        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})
        LayerRelation.objects.create(
            name='cities',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=crud_view.layer,
            settings={"distance": 100}
        )
        self.feature.save()

        self.feature.refresh_from_db()
        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})

        feature_intersect = Feature.objects.create(
            layer=layer,
            properties={},
            geom=LineString((0, 0), (10, 0))
        )

        self.feature.refresh_from_db()
        self.feature.save()
        self.feature.refresh_from_db()

        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0, 'cities': []})

        feature_intersect.properties = {'name': 'City'}
        feature_intersect.save()

        self.feature.refresh_from_db()
        self.feature.save()
        self.feature.refresh_from_db()

        self.assertEqual(self.feature.properties, {'name': 'toto', 'length': 1.0, 'cities': ['City']})

    def test_signal_start_end_cities(self, property_mocked, async_mocked, mock_delay):
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)

        layer = LayerFactory.create(geom_type=GeometryTypes.Polygon,
                                    schema={"type": "object",
                                            "required": ["name", ],
                                            "properties": {"name": {"type": "string", "title": "Name"}}
                                            })
        crud_view = CrudViewFactory.create(layer=layer)
        LayerRelation.objects.create(
            name='cities',
            relation_type='intersects',
            origin=self.crud_view.layer,
            destination=crud_view.layer
        )

        self.prop_relation_first_city = CrudViewProperty.objects.create(
            view=self.crud_view, key="first_city",
            editable=False,
            json_schema={'type': "string"},
            function_path='test_terra_geocrud.functions_test.get_first_city'
        )

        self.prop_relation_last_city = CrudViewProperty.objects.create(
            view=self.crud_view, key="last_city",
            editable=False,
            json_schema={'type': "string"},
            function_path='test_terra_geocrud.functions_test.get_last_city'
        )

        sync_layer_schema(self.crud_view)
        sync_layer_schema(crud_view)

        self.feature_long.refresh_from_db()
        self.feature_long.save()
        self.feature_long.refresh_from_db()

        self.assertEqual(self.feature_long.properties, {'name': 'tata', 'first_city': '', 'last_city': ''})

        Feature.objects.create(
            layer=layer,
            properties={"name": "Ville 0 0"},
            geom=Polygon(((0, 0), (5, 0),
                         (5, 5), (0, 5),
                         (0, 0))),

        )
        Feature.objects.create(
            layer=layer,
            properties={"name": "Ville 5 5"},
            geom=Polygon(((5, 5), (10, 5),
                         (10, 10), (5, 10),
                         (5, 5)))
        )
        self.feature_long.refresh_from_db()
        self.feature_long.save()
        self.feature_long.refresh_from_db()

        feature = Feature.objects.get(pk=self.feature_long.pk)
        self.assertEqual(feature.properties, {'first_city': 'Ville 0 0', 'last_city': 'Ville 5 5', 'name': 'tata'})


@patch('terra_geocrud.signals.execute_async_func')
@patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock)
class RelationChangeCalculatedPropertiesTest(AsyncSideEffect, TestCase):
    def setUp(self):

        layer = LayerFactory.create(geom_type=GeometryTypes.LineString,
                                    schema={"type": "object",
                                            "required": ["name", ],
                                            "properties": {"name": {"type": "string", "title": "Name"}}
                                            })
        self.crud_view = CrudViewFactory(layer=layer)
        self.layer_city = LayerFactory.create(geom_type=GeometryTypes.Polygon,
                                              schema={"type": "object",
                                                      "required": ["name", ],
                                                      "properties": {"name": {"type": "string", "title": "Name"}}
                                                      })
        crud_view = CrudViewFactory.create(layer=self.layer_city)
        with patch('terra_geocrud.tasks.feature_update_relations_destinations.delay'):
            self.layer_relation = LayerRelation.objects.create(
                name='cities',
                relation_type='intersects',
                origin=self.crud_view.layer,
                destination=crud_view.layer
            )

        self.prop_name = CrudViewProperty.objects.create(
            view=self.crud_view, key="name",
            editable=True,
            json_schema={'type': "string", "title": "Name"}
        )
        self.prop_relation_first_city = CrudViewProperty.objects.create(
            view=self.crud_view, key="city",
            editable=False,
            json_schema={'type': "array", "items": {"type": "string"}},
            function_path='test_terra_geocrud.functions_test.get_cities'
        )
        sync_layer_schema(self.crud_view)
        sync_layer_schema(crud_view)
        with patch('terra_geocrud.signals.execute_async_func') as mocked_async:
            self.add_side_effect_async(mocked_async)
            with patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock) as mocked:
                mocked.return_value = True
                self.feature = Feature.objects.create(
                    layer=self.crud_view.layer,
                    properties={'name': 'toto'},
                    geom=LineString((0, 0), (1, 0))
                )
                self.feature_long = Feature.objects.create(
                    layer=self.crud_view.layer,
                    properties={'name': 'tata'},
                    geom=LineString((0, 0), (10, 10))
                )
        Feature.objects.create(
            layer=self.layer_city,
            properties={"name": "Ville 0 0"},
            geom=Polygon(((0, 0), (5, 0),
                         (5, 5), (0, 5),
                         (0, 0))),

        )
        Feature.objects.create(
            layer=self.layer_city,
            properties={"name": "Ville 5 5"},
            geom=Polygon(((5, 5), (10, 5),
                         (10, 10), (5, 10),
                         (5, 5)))
        )

        Feature.objects.create(
            layer=self.layer_city,
            properties={"name": "Ville 11 11"},
            geom=Polygon(((11, 11), (12, 11),
                         (12, 12), (11, 12),
                         (11, 11)))
        )

    @patch('terra_geocrud.tasks.feature_update_relations_destinations.delay')
    def test_signal_layer_relation_create(self, async_delay, property_mocked, async_mocked):
        def side_effect_async(feature_id, kwargs):
            feature_update_relations_destinations(feature_id, kwargs)
        async_delay.side_effect = side_effect_async
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)

        self.feature_long.save()
        self.feature_long.refresh_from_db()
        self.assertEqual(self.feature_long.properties, {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})

        layer_relation = LayerRelation.objects.get(pk=self.layer_relation.pk)
        layer_relation.relation_type = 'distance'
        layer_relation.settings = {"distance": 1000000}
        layer_relation.save()

        self.feature_long.refresh_from_db()
        self.assertEqual(self.feature_long.properties, {'city': ['Ville 0 0', 'Ville 5 5', 'Ville 11 11'], 'name': 'tata'})

    @patch('terra_geocrud.tasks.feature_update_relations_destinations.delay')
    def test_signal_destination_create(self, async_delay, property_mocked, async_mocked):
        def side_effect_async(feature_id, kwargs):
            feature_update_relations_destinations(feature_id, kwargs)
        async_delay.side_effect = side_effect_async
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        self.feature_long.save()

        Feature.objects.create(
            layer=self.layer_city,
            properties={"name": "Ville 0 0 2"},
            geom=Polygon(((0, 0), (5, 0),
                          (5, 5), (0, 5),
                          (0, 0)))
        )
        self.feature_long.refresh_from_db()

        self.assertEqual(self.feature_long.properties, {'city': ['Ville 0 0', 'Ville 5 5', 'Ville 0 0 2'], 'name': 'tata'})

    @patch('terra_geocrud.tasks.feature_update_relations_destinations.delay')
    @patch('terra_geocrud.tasks.feature_update_relations_origins.delay')
    def test_signal_destination_delete(self, async_delay_origins, async_delay_destinations, property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            feature_update_relations_destinations(feature_id, kwargs)

        def side_effect_async_origins(feature_id, kwargs):
            feature_update_relations_origins(feature_id, kwargs)

        async_delay_destinations.side_effect = side_effect_async_destinations
        async_delay_origins.side_effect = side_effect_async_origins
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        self.feature_long.save()

        feature = Feature.objects.create(
            layer=self.layer_city,
            properties={"name": "Ville 0 0 2"},
            geom=Polygon(((0, 0), (5, 0),
                          (5, 5), (0, 5),
                          (0, 0)))
        )
        feature.delete()
        self.feature_long.refresh_from_db()

        self.assertEqual(self.feature_long.properties, {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})

    @patch('terra_geocrud.tasks.feature_update_relations_destinations.delay')
    @patch('terra_geocrud.tasks.feature_update_relations_origins.delay')
    def test_signal_feature_deleted_before_delay(self, async_delay_origins, async_delay_destinations, property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            Feature.objects.get(pk=feature_id).delete()
            task_result = feature_update_relations_destinations(feature_id, kwargs)
            assert not task_result

        def side_effect_async_origins(feature_id, kwargs):
            feature_update_relations_origins(feature_id, kwargs)

        async_delay_destinations.side_effect = side_effect_async_destinations
        async_delay_origins.side_effect = side_effect_async_origins
        property_mocked.return_value = True

        self.add_side_effect_async(async_mocked)
        self.feature_long.save()
        feature = Feature.objects.create(
            layer=self.layer_city,
            properties={"name": "Ville 0 0 2"},
            geom=Polygon(((0, 0), (5, 0),
                          (5, 5), (0, 5),
                          (0, 0)))
        )
        feature.delete()

    @patch('terra_geocrud.tasks.feature_update_relations_destinations.delay')
    def test_signal_layer_relation_create_deleted_before_delay(self, async_delay, property_mocked, async_mocked):
        def side_effect_async_delay(relation_id, kwargs):
            feature_update_relations_destinations(relation_id, kwargs)

        self.add_side_effect_async(async_mocked)
        async_delay.side_effect = side_effect_async_delay
        property_mocked.return_value = True
        self.feature_long.save()
        self.feature_long.refresh_from_db()

        def side_effect_async(async_func, args=()):
            LayerRelation.objects.get(pk=args[0]).delete()
            result_delay = async_func(*args)
            assert not result_delay

        async_mocked.side_effect = side_effect_async

        self.assertEqual(self.feature_long.properties, {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})

        layer_relation = LayerRelation.objects.get(pk=self.layer_relation.pk)
        layer_relation.relation_type = 'distance'
        layer_relation.settings = {"distance": 1000000}
        layer_relation.save()

        self.feature_long.refresh_from_db()
        self.assertEqual(self.feature_long.properties, {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})
