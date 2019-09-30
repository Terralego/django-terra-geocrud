from django.core.management import call_command
from django.test.testcases import TestCase

from geostore import GeometryTypes
from geostore.models import Layer
from terra_geocrud.models import CrudView


class CreateDefaultCrudViewTestCase(TestCase):
    def setUp(self):
        self.layer_1 = Layer.objects.create(name='1', geom_type=GeometryTypes.Point)
        self.layer_2 = Layer.objects.create(name='2', geom_type=GeometryTypes.LineString)

    def test_views_created(self):
        call_command('create_default_crud_views')

        self.assertTrue(CrudView.objects.filter(layer__pk__in=[self.layer_1.pk, self.layer_2.pk]).exists())

    def test_views_not_created_if_already_exists(self):
        layer_3 = Layer.objects.create(name='3', geom_type=GeometryTypes.Polygon)
        CrudView.objects.create(name=layer_3.name, layer=layer_3, order=0)

        call_command('create_default_crud_views')
        self.assertEqual(CrudView.objects.count(), 3)
