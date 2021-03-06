from unittest.case import skipIf

from django.test import TestCase
from geostore.models import LayerExtraGeom, FeatureExtraGeom, Feature
from geostore.settings import GEOSTORE_EXPORT_CELERY_ASYNC

from terra_geocrud import models
from terra_geocrud.properties.schema import sync_layer_schema, sync_ui_schema
from terra_geocrud.serializers import CrudFeatureExtraGeomSerializer, CrudFeatureDetailSerializer, CrudViewSerializer
from terra_geocrud.tests import factories
from terra_geocrud.tests.factories import CrudViewFactory


class CrudFeatureExtraGeomSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.view = CrudViewFactory()
        self.extra_layer = LayerExtraGeom.objects.create(layer=self.view.layer,
                                                         title="extra")
        self.feature = Feature.objects.create(layer=self.view.layer,
                                              geom='POINT(0 0)')
        self.extra_geometry = FeatureExtraGeom.objects.create(feature=self.feature,
                                                              layer_extra_geom=self.extra_layer,
                                                              geom='POINT(0 0)')

    def test_serializer_output_same_as_feature_serializer(self):
        serializer = CrudFeatureExtraGeomSerializer(self.extra_geometry)
        self.assertDictEqual(serializer.data,
                             CrudFeatureDetailSerializer(self.feature).data)


class CrudFeatureSerializer(TestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        models.CrudViewProperty.objects.create(
            view=self.crud_view,
            key="date_start",
            required=True,
            json_schema={
                'type': "string",
                "title": "Date start",
                "format": "date"
            }
        )
        models.CrudViewProperty.objects.create(
            view=self.crud_view,
            key="date_end",
            required=True,
            json_schema={
                'type': "string",
                "title": "Date end",
                "format": "date"
            }
        )
        self.feature = Feature.objects.create(geom='POINT(0 0)',
                                              properties={
                                                  "date_start": "test",
                                                  "date_end": "2020-12-10"
                                              },
                                              layer=self.crud_view.layer)
        sync_layer_schema(self.crud_view)
        sync_ui_schema(self.crud_view)
        self.serializer = CrudFeatureDetailSerializer(self.feature)

    def test_formatted_right_date(self):
        """ ISO stored date format should be formatted in display_properties """
        display_value = self.serializer.data['display_properties']['__default__']['properties']['date_end']['display_value']
        self.assertEqual('12/10/2020', display_value)

    def test_formatted_wrong_date(self):
        """ Bad value should not raise exception when formatting attempt """
        display_value = self.serializer.data['display_properties']['__default__']['properties']['date_start']['display_value']
        self.assertEqual('test', display_value)


class CrudViewSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crud_view = factories.CrudViewFactory()
        sync_layer_schema(cls.crud_view)
        sync_ui_schema(cls.crud_view)

    @skipIf(not GEOSTORE_EXPORT_CELERY_ASYNC, 'Test with export sync only')
    def test_exports_with_async_mode(self,):
        serializer = CrudViewSerializer(self.crud_view)
        data = serializer.data
        self.assertDictEqual(data['exports'], {
            "GeoJSON": f"/api/crud/layers/{self.crud_view.layer_id}/geojson/",
            "KML": f"/api/crud/layers/{self.crud_view.layer_id}/kml/",
            "Shape": f"/api/crud/layers/{self.crud_view.layer_id}/shapefile_async/",
        })

    @skipIf(GEOSTORE_EXPORT_CELERY_ASYNC, 'Test with export async only')
    def test_exports_without_async_mode(self):
        serializer = CrudViewSerializer(self.crud_view)
        data = serializer.data
        self.assertIsNone(data['exports'], data)
