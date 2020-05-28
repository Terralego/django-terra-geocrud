from django.test import TestCase
from geostore.models import LayerExtraGeom, FeatureExtraGeom, Feature
from terra_geocrud.serializers import CrudFeatureExtraGeomSerializer, CrudFeatureDetailSerializer

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
