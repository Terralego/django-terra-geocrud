from unittest import mock

from django.db.models import signals

from ..properties.schema import sync_layer_schema
from unittest.mock import patch, PropertyMock

from geostore import GeometryTypes
from geostore.models import Feature, LayerRelation
from geostore.tests.factories import LayerFactory
from django.test import TestCase, override_settings

from django.contrib.gis.geos import LineString, Polygon

from terra_geocrud.models import CrudViewProperty
from terra_geocrud.properties.files import get_storage, store_feature_files
from terra_geocrud.tasks import (
    ConcurrentPropertyModificationError,
    feature_update_relations_and_properties,
    feature_update_relations_origins,
    feature_update_destination_properties,
    sync_properties_relations_destination,
)
from terra_geocrud.thumbnail_backends import ThumbnailDataFileBackend

from terra_geocrud.tests.factories import CrudViewFactory
from ..signals import save_feature

thumbnail_backend = ThumbnailDataFileBackend()


class AsyncSideEffect(object):
    def add_side_effect_async(self, mocked):
        def side_effect_async(async_func, args=()):
            async_func(*args)
        mocked.side_effect = side_effect_async


@patch('terra_geocrud.tasks.feature_update_relations_and_properties.delay')
@patch('terra_geocrud.signals.execute_async_func')
class DeletionFeatureDeletePictureTest(TestCase):
    def setUp(self):

        layer = LayerFactory.create(geom_type=GeometryTypes.LineString,
                                    schema={"type": "object",
                                            "required": ["name", ],
                                            "properties": {"name": {"type": "string", "title": "Name"}}
                                            })
        self.crud_view = CrudViewFactory(layer=layer)
        self.prop_name = CrudViewProperty.objects.create(
            view=self.crud_view, key="picture",
            editable=True,
            json_schema={'type': "string",
                         'title': "Picture",
                         'format': "data-url"}
        )
        sync_layer_schema(self.crud_view)
        self.feature = Feature.objects.create(
            layer=self.crud_view.layer,
            properties={'name': 'foo',
                        'picture': "data:image/png;name=titre_laromieu-fondblanc.jpg;base64,iVBORw0KGgoAAAANSUhEUgAAAA"
                                   "EAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="},
            geom=LineString((0, 0), (1, 0))
        )
        store_feature_files(self.feature, {})
        self.storage = get_storage()
        self.property_value = self.feature.properties.get('picture')
        self.storage_file_path = self.property_value.split(';name=')[-1].split(';')[0]
        self.thumbnail = thumbnail_backend.get_thumbnail(self.storage_file_path, "500x500", crop='noop', upscale=False)
        self.assertTrue(self.storage.exists(self.thumbnail.name))
        self.assertTrue(self.storage.exists(self.storage_file_path))

    def test_signal_feature_delete_pictures(self, async_mocked, mock_delay):
        self.feature.delete()
        self.assertFalse(self.storage.exists(self.thumbnail.name))
        self.assertFalse(self.storage.exists(self.storage_file_path))


@patch('terra_geocrud.tasks.feature_update_relations_and_properties.delay')
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

    def test_signal_property_update(self, property_mocked, async_mocked, mock_delay):
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


class ConcurrentPropertiesTest(AsyncSideEffect, TestCase):
    def setUp(self):
        self.test_value = "PotatoSalad"
        self.layer = LayerFactory.create(
            geom_type=GeometryTypes.LineString,
            schema={
                "type": "object",
                "required": [
                    "name",
                ],
                "properties": {"name": {"type": "string", "title": "Name"}},
            },
        )
        self.crud_view = CrudViewFactory(layer=self.layer)
        CrudViewProperty.objects.create(
            view=self.crud_view,
            key="length",
            editable=False,
            json_schema={"type": "integer", "title": "Length"},
            function_path="test_terra_geocrud.functions_test.get_length_km",
        )
        CrudViewProperty.objects.create(
            view=self.crud_view,
            key="name",
            editable=True,
            json_schema={"type": "string", "title": "Name"},
        )
        self.test_prop = CrudViewProperty.objects.create(
            view=self.crud_view,
            key="test_property",
            editable=True,
            json_schema={"type": "string", "title": "Test Property"},
        )
        sync_layer_schema(self.crud_view)

        self.new_object = Feature.objects.create(
            layer=self.crud_view.layer,
            properties={"name": "super test"},
            geom=LineString((0, 0), (1, 0)),
        )

    @mock.patch("terra_geocrud.signals.execute_async_func")
    @mock.patch(
        "geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC", new_callable=PropertyMock
    )
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_concurrent_writes_in_async_ctx(
        self, mocked_setting, mocked_execute_async_func
    ):
        """
        Test that an object modification while it is being used in an async signal handler does not result in data loss.

        To create a concurrency issue, we patch 'tasks.sync_properties_relations_destination' with a wrapper.
        'tasks.sync_properties_relations_destination' is usually called in a celery task, by wrapping it we can modify
        the database to emulate a concurrent write to the underlying feature that is being updated.
        """

        self.add_side_effect_async(mocked_execute_async_func)

        def wrapped_sync_properties_relations_destination(*args, **kwargs):
            def inject_property_modification(pk, key, value):
                f = Feature.objects.get(pk=pk)
                f.properties[key] = value
                signals.post_save.disconnect(save_feature, sender=Feature)
                f.save()
                signals.post_save.connect(save_feature, sender=Feature)

            # If the argument is our test object => modify it's database instance to create a data race
            if args[0].pk == self.new_object.pk:
                inject_property_modification(
                    args[0].pk, self.test_prop.key, self.test_value
                )
            return sync_properties_relations_destination(*args, **kwargs)

        """ Patch using a context manager instead of a function decorator : otherwise we can't access the original function
        to call it since it has been mocked. """
        with patch(
            "terra_geocrud.tasks.sync_properties_relations_destination"
        ) as mocked_sync_properties_relations_destination:
            # Update geometry to trigger properties computations
            mocked_sync_properties_relations_destination.side_effect = (
                wrapped_sync_properties_relations_destination
            )
            self.new_object.geom = LineString((0, 1), (1, 0))
            self.new_object.save()
            mocked_sync_properties_relations_destination.assert_called()

        self.assertEqual(
            Feature.objects.get(pk=self.new_object.pk).properties[self.test_prop.key],
            self.test_value,
        )
        self.assertTrue(
            "length" in Feature.objects.get(pk=self.new_object.pk).properties
        )

    @mock.patch("terra_geocrud.signals.execute_async_func")
    @mock.patch(
        "geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC", new_callable=PropertyMock
    )
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_concurrent_delete_in_async_ctx(
        self, mocked_setting, mocked_execute_async_func
    ):
        """
        Test that an object deletion while it is being used in an async signal handler results in an exception.

        See 'test_concurrent_writes_in_async_ctx' for more details on the inner workings of this test.
        """

        self.add_side_effect_async(mocked_execute_async_func)

        def wrapped_sync_properties_relations_destination(*args, **kwargs):
            def inject_feature_deletion(pk):
                f = Feature.objects.get(pk=pk)
                f.delete()

            # If the argument is our test object => modify it's database instance to create a data race
            if args[0].pk == self.new_object.pk:
                inject_feature_deletion(args[0].pk)
            return sync_properties_relations_destination(*args, **kwargs)

        """ Patch using a context manager instead of a function decorator : otherwise we can't access the original function
        to call it since it has been mocked. """
        with patch(
            "terra_geocrud.tasks.sync_properties_relations_destination"
        ) as mocked_sync_properties_relations_destination:
            with self.assertRaises(Feature.DoesNotExist):
                # Update geometry to trigger properties computations
                mocked_sync_properties_relations_destination.side_effect = (
                    wrapped_sync_properties_relations_destination
                )
                self.new_object.geom = LineString((0, 1), (1, 0))
                self.new_object.save()
                mocked_sync_properties_relations_destination.assert_called()

    @mock.patch("terra_geocrud.signals.execute_async_func")
    @mock.patch(
        "geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC", new_callable=PropertyMock
    )
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_concurrent_property_modification_in_async_ctx(
        self, mocked_setting, mocked_execute_async_func
    ):
        """
        Test that if the property of a json field is modified concurrently an exception is raised.

        See 'test_concurrent_writes_in_async_ctx' for more details on the inner workings of this test.
        """

        self.add_side_effect_async(mocked_execute_async_func)

        def wrapped_sync_properties_relations_destination(*args, **kwargs):
            def inject_property_modification(pk, key, value):
                f = Feature.objects.get(pk=pk)
                f.properties[key] = value
                signals.post_save.disconnect(save_feature, sender=Feature)
                f.save()
                signals.post_save.connect(save_feature, sender=Feature)

            # If the argument is our test object => modify it's database instance to create a data race
            if args[0].pk == self.new_object.pk:
                inject_property_modification(args[0].pk, "length", 42)
            return sync_properties_relations_destination(*args, **kwargs)

        """ Patch using a context manager instead of a function decorator : otherwise we can't access the original function
        to call it since it has been mocked. """
        with patch(
            "terra_geocrud.tasks.sync_properties_relations_destination"
        ) as mocked_sync_properties_relations_destination:
            with self.assertRaises(ConcurrentPropertyModificationError):
                # Update geometry to trigger properties computations
                mocked_sync_properties_relations_destination.side_effect = (
                    wrapped_sync_properties_relations_destination
                )
                self.new_object.geom = LineString((0, 1), (1, 0))
                self.new_object.save()
                mocked_sync_properties_relations_destination.assert_called()


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
        with patch('terra_geocrud.tasks.feature_update_relations_and_properties.delay'):
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
        self.feature_city_first = Feature.objects.create(
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

    @patch('terra_geocrud.tasks.feature_update_relations_and_properties.delay')
    def test_signal_layer_relation_create(self, async_delay, property_mocked, async_mocked):
        def side_effect_async(feature_id, kwargs):
            feature_update_relations_and_properties(feature_id, kwargs)
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

    @patch('terra_geocrud.tasks.feature_update_relations_and_properties.delay')
    def test_signal_destination_create(self, async_delay, property_mocked, async_mocked):
        def side_effect_async(feature_id, kwargs):
            feature_update_relations_and_properties(feature_id, kwargs)
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

    @patch('terra_geocrud.tasks.feature_update_relations_and_properties.delay')
    @patch('terra_geocrud.tasks.feature_update_relations_origins.delay')
    def test_signal_destination_delete(self, async_delay_origins, async_delay_destinations, property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            feature_update_relations_and_properties(feature_id, kwargs)

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

    @patch('terra_geocrud.tasks.feature_update_relations_and_properties.delay')
    @patch('terra_geocrud.signals.feature_update_relations_origins')
    def test_signal_relations_feature_deleted_before_delay(self, async_delay_origins, async_delay_destinations,
                                                           property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            Feature.objects.get(pk=feature_id).delete()
            task_result = feature_update_relations_and_properties(feature_id, kwargs)
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
        # Delete feature and 2 linestring in side_effect_async_destinations
        self.assertEqual(async_delay_origins.call_count, 3)
        # Change 2 linestrings props
        self.assertEqual(async_delay_destinations.call_count, 2)

    @patch('terra_geocrud.signals.feature_update_destination_properties')
    def test_signal_properties_feature_deleted_before_delay(self, async_delay_destinations, property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            Feature.objects.get(pk=feature_id).delete()
            task_result = feature_update_destination_properties(feature_id, kwargs)
            assert not task_result

        async_delay_destinations.side_effect = side_effect_async_destinations
        property_mocked.return_value = True

        self.add_side_effect_async(async_mocked)
        self.feature_long.save(update_fields=['properties'])
        async_delay_destinations.assert_called_once()

    @patch('terra_geocrud.signals.feature_update_relations_and_properties')
    @patch('terra_geocrud.signals.feature_update_destination_properties')
    def test_signal_feature_save_change_name_revert_relation(self, async_delay_destinations, async_delay_relations_props,
                                                             property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            feature_update_destination_properties(feature_id, kwargs)

        def side_effect_async_relations(feature_id, kwargs):
            feature_update_relations_and_properties(feature_id, kwargs)

        async_delay_destinations.side_effect = side_effect_async_destinations
        async_delay_relations_props.side_effect = side_effect_async_relations
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        self.feature_long.save()
        self.feature_long.refresh_from_db()
        async_delay_relations_props.assert_called_once()
        async_delay_destinations.assert_not_called()
        self.assertEqual(self.feature_long.properties,
                         {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})

        self.feature_city_first.properties['name'] = "City 0 0"

        self.feature_city_first.save(update_fields=["properties"])
        self.feature_long.refresh_from_db()

        self.assertEqual(self.feature_long.properties, {'city': ['City 0 0', 'Ville 5 5'], 'name': 'tata'})
        async_delay_destinations.assert_called_once()
        async_delay_relations_props.assert_called_once()

    @patch('terra_geocrud.signals.feature_update_relations_and_properties')
    @patch('terra_geocrud.signals.feature_update_destination_properties')
    def test_signal_feature_save_change_geom(self, async_delay_destinations, async_delay_relations_props,
                                             property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            feature_update_destination_properties(feature_id, kwargs)

        def side_effect_async_relations(feature_id, kwargs):
            feature_update_relations_and_properties(feature_id, kwargs)

        async_delay_destinations.side_effect = side_effect_async_destinations
        async_delay_relations_props.side_effect = side_effect_async_relations
        property_mocked.return_value = True

        self.add_side_effect_async(async_mocked)
        self.feature_long.save()

        self.feature_long.refresh_from_db()
        async_delay_relations_props.assert_called_once()
        async_delay_destinations.assert_not_called()

        self.assertEqual(self.feature_long.properties,
                         {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})

        self.feature_long.geom = LineString((0, 0), (1, 0))

        self.feature_long.save(update_fields=["geom"])
        self.feature_long.refresh_from_db()

        self.assertEqual(self.feature_long.properties, {'city': ['Ville 0 0'], 'name': 'tata'})
        self.assertEqual(async_delay_relations_props.call_count, 2)

    @patch('terra_geocrud.signals.feature_update_relations_and_properties')
    @patch('terra_geocrud.signals.feature_update_destination_properties')
    def test_signal_feature_save_change_geom_empty_update_fields(self, async_delay_destinations, async_delay_relations_props,
                                                                 property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            feature_update_destination_properties(feature_id, kwargs)

        def side_effect_async_relations(feature_id, kwargs):
            feature_update_relations_and_properties(feature_id, kwargs)

        async_delay_destinations.side_effect = side_effect_async_destinations
        async_delay_relations_props.side_effect = side_effect_async_relations
        property_mocked.return_value = True

        self.add_side_effect_async(async_mocked)
        self.feature_long.save()

        self.feature_long.refresh_from_db()
        async_delay_relations_props.assert_called_once()
        async_delay_destinations.assert_not_called()

        self.assertEqual(self.feature_long.properties,
                         {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})

        self.feature_long.geom = LineString((0, 0), (1, 0))
        self.assertEqual(async_delay_relations_props.call_count, 1)
        self.feature_long.save(update_fields=[])
        self.feature_long.refresh_from_db()

        self.assertEqual(self.feature_long.properties, {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})
        self.assertEqual(async_delay_relations_props.call_count, 1)

    @patch('terra_geocrud.signals.feature_update_relations_and_properties')
    @patch('terra_geocrud.signals.feature_update_destination_properties')
    def test_signal_feature_save_change_geom_revert_relation(self, async_delay_destinations, async_delay_relations_props,
                                                             property_mocked, async_mocked):
        def side_effect_async_destinations(feature_id, kwargs):
            feature_update_destination_properties(feature_id, kwargs)

        def side_effect_async_relations(feature_id, kwargs):
            feature_update_relations_and_properties(feature_id, kwargs)

        async_delay_destinations.side_effect = side_effect_async_destinations
        async_delay_relations_props.side_effect = side_effect_async_relations
        property_mocked.return_value = True
        self.add_side_effect_async(async_mocked)
        self.feature_long.save()
        self.feature_long.refresh_from_db()
        self.assertEqual(self.feature_long.properties,
                         {'city': ['Ville 0 0', 'Ville 5 5'], 'name': 'tata'})

        self.feature_city_first.properties['name'] = "City 0 0"
        self.feature_city_first.save(update_fields=["properties"])
        async_delay_destinations.assert_called()
        self.feature_long.refresh_from_db()

        self.assertEqual(self.feature_long.properties, {'city': ['City 0 0', 'Ville 5 5'], 'name': 'tata'})

    @patch('terra_geocrud.tasks.feature_update_relations_and_properties.delay')
    def test_signal_layer_relation_create_deleted_before_delay(self, async_delay, property_mocked, async_mocked):
        def side_effect_async_delay(relation_id, kwargs):
            feature_update_relations_and_properties(relation_id, kwargs)

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
