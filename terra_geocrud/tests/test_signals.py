from geostore import GeometryTypes
from geostore.models import Layer, LayerExtraGeom, Feature, FeatureExtraGeom
from geostore.tests.factories import LayerFactory
from django.test import TestCase
from django.contrib.gis.geos import Point, LineString

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
        self.prop_name = CrudViewProperty.objects.create(
            view=self.crud_view, key="length",
            editable=False,
            json_schema={'type': "integer", "title": "Length"},
            function_path='test_terra_geocrud.functions_test.get_length'
        )
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
