import json
import os
from base64 import b64encode
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from geostore import GeometryTypes
from io import BytesIO
from rest_framework import status
from rest_framework.test import APITestCase

from geostore.models import Feature
from terra_geocrud import settings as app_settings
from terra_geocrud.models import FeaturePropertyDisplayGroup
from terra_geocrud.tests import factories
from .settings import (FEATURE_PROPERTIES, LAYER_COMPOSANTES_SCHEMA,
                       SNAPSHOT_PLAN_DE_GESTION)
from .. import models


class CrudGroupViewSetTestCase(APITestCase):
    def setUp(self):
        self.group = models.CrudGroupView.objects.create(name="group", order=0)

    def test_list_endpoint(self):
        response = self.client.get(reverse('terra_geocrud:crudgroupview-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), models.CrudGroupView.objects.count())

        self.assertEqual(data[0]['id'], self.group.pk)

    def test_detail_endpoint(self):
        response = self.client.get(reverse('terra_geocrud:crudgroupview-detail', args=(self.group.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['id'], self.group.pk)


class CrudViewViewSetTestCase(APITestCase):
    def setUp(self):
        self.group_1 = models.CrudGroupView.objects.create(name="group 1", order=0)
        self.group_2 = models.CrudGroupView.objects.create(name="group 2", order=1)
        self.view_1 = factories.CrudViewFactory(name="View 1", order=0, group=self.group_1)
        self.view_2 = factories.CrudViewFactory(name="View 2", order=0, group=self.group_2)
        self.view_3 = factories.CrudViewFactory(name="View 3", order=1, group=self.group_2)

    def test_list_endpoint(self):
        response = self.client.get(reverse('terra_geocrud:crudview-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), models.CrudView.objects.count())

        self.assertEqual(data[0]['id'], self.view_1.pk)

    def test_detail_endpoint(self):
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['id'], self.view_1.pk)

    def test_default_point_style(self):
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.Point)
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], app_settings.TERRA_GEOCRUD['STYLES']['point'])

    def test_override_point_style(self):
        custom_style = {
            'type': 'circle',
            'paint': {
                'circle-color': '#FFFFFF',
                'circle-radius': 25
            }
        }
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.MultiPoint,
                                              map_style=custom_style)
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], custom_style)

    def test_default_line_style(self):
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.LineString)
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], app_settings.TERRA_GEOCRUD['STYLES']['line'])

    def test_override_line_style(self):
        custom_style = {
            'type': 'line',
            'paint': {
                'line-color': '#000',
                'line-width': 3
            }
        }
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.MultiLineString,
                                              map_style=custom_style)
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], custom_style)

    def test_default_polygon_style(self):
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.Polygon)
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], app_settings.TERRA_GEOCRUD['STYLES']['polygon'])

    def test_override_polygon_style(self):
        custom_style = {
            'type': 'fill',
            'paint': {
                'fill-color': '#000'
            }
        }
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.MultiPolygon,
                                              map_style=custom_style)
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], custom_style)

    def test_original_ui_schema(self):
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['ui_schema'], self.view_1.ui_schema)

    def test_grouped_ui_schema(self):
        self.view_1.ui_schema = {
            'name': {'ui-widget': 'textarea'},
            'ui-order': ['name', 'age']
        }
        self.view_1.save()
        group_1 = FeaturePropertyDisplayGroup.objects.create(crud_view=self.view_1, label='test',
                                                             properties=['age'])
        group_2 = FeaturePropertyDisplayGroup.objects.create(crud_view=self.view_1, label='test2',
                                                             properties=['name'])
        response = self.client.get(reverse('terra_geocrud:crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(
            data['ui_schema'],
            {'ui-order': [],
             'test': {'ui-order': ['age', '*']},
             'test2': {'ui-order': ['name', '*'],
                       'name': {'ui-widget': 'textarea'}}}
        )
        group_1.delete()
        group_2.delete()


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class CrudSettingsViewTestCase(TestCase):
    def setUp(self):
        self.group_1 = models.CrudGroupView.objects.create(name="group 1", order=0)
        self.group_2 = models.CrudGroupView.objects.create(name="group 2", order=1)
        self.view_1 = factories.CrudViewFactory(name="View 1", order=0, group=self.group_1)
        self.view_2 = factories.CrudViewFactory(name="View 2", order=0, group=self.group_2)
        self.view_3 = factories.CrudViewFactory(name="View 3", order=1, group=self.group_2)
        self.response = self.client.get(reverse('terra_geocrud:settings'))

    def test_endpoint_access(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_endpoint_menu(self):
        """
        Menu has 1 section per group, and 1 section for non grouped views
        """
        data = self.response.json()
        self.assertEqual(len(data['menu']), models.CrudGroupView.objects.count() + 1)

    def test_endpoint_config_without_settings(self):
        """
        Without extra settings, config section is empty
        """
        data = self.response.json()
        self.assertDictEqual(data['config'], app_settings._DEFAULT_TERRA_GEOCRUD)

    @override_settings(TERRA_GEOCRUD={"EXTENT": [[0, 90], [90, 180]]})
    def test_endpoint_config_with_settings(self):
        """
        Extra TERRA_GEOCRUD settings are added to config section
        """
        self.response = self.client.get(reverse('terra_geocrud:settings'))
        data = self.response.json()
        self.assertEqual(data['config']['EXTENT'], [[0, 90], [90, 180]])


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class CrudRenderTemplateDetailViewTestCase(APITestCase):
    def setUp(self):
        self.crud_view = factories.CrudViewFactory(name="Composantes", order=0,
                                                   layer__schema=json.load(open(LAYER_COMPOSANTES_SCHEMA)))

        self.feature = Feature.objects.create(
            layer=self.crud_view.layer,
            geom=Point(x=-0.246322800072846, y=44.5562461167907),
            properties=json.load(open(FEATURE_PROPERTIES)),
        )
        self.template = factories.TemplateDocxFactory.create(
            name='Template',
        )
        self.crud_view.templates.add(self.template)

    def test_template_rendering(self):
        response = self.client.get(
            reverse(
                'terra_geocrud:render-template',
                kwargs={'pk': self.feature.pk, 'template_pk': self.template.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response._headers['content-type'][-1],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        with open(SNAPSHOT_PLAN_DE_GESTION) as reader:
            content_xml = reader.read().encode('utf-8')
        buffer = BytesIO(response.content)
        with ZipFile(buffer) as archive:
            with archive.open(os.path.join('word', 'document.xml')) as reader:
                self.assertEqual(reader.read(), content_xml)


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class CrudFeatureViewsSetTestCase(APITestCase):
    def setUp(self):
        self.crud_view = factories.CrudViewFactory()
        self.group_1 = FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test',
                                                                  properties=['age'])
        self.group_2 = FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test2',
                                                                  properties=['name'])
        self.feature = Feature.objects.create(geom=Point(0, 0, srid=4326),
                                              properties={"age": 10, "name": "jec", "country": "slovenija"},
                                              layer=self.crud_view.layer)
        self.template = factories.TemplateDocxFactory()
        self.crud_view.templates.add(self.template)

    def test_list_endpoint(self):
        response_list = self.client.get(reverse('terra_geocrud:feature-list', args=(self.crud_view.layer_id,)),
                                        format="json")
        data = response_list.json()
        self.assertEqual(len(data), self.crud_view.layer.features.count())

    def test_property_detail_display_with_groups(self):
        response_detail = self.client.get(reverse('terra_geocrud:feature-detail',
                                                  args=(self.crud_view.layer_id,
                                                        self.feature.identifier)),
                                          format="json")
        data = response_detail.json()
        expected_keys = list(self.crud_view.feature_display_groups.all()
                             .values_list('slug', flat=True)) + ['__default__']
        self.assertEqual(list(data['display_properties'].keys()), expected_keys)

    def test_property_detail_documents(self):
        response_detail = self.client.get(reverse('terra_geocrud:feature-detail',
                                                  args=(self.crud_view.layer_id,
                                                        self.feature.identifier)),
                                          format="json")
        data = response_detail.json()
        self.assertEqual(len(data['documents']), self.crud_view.templates.count())


class CrudFeatureFileAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        self.crud_view_file = factories.CrudViewFactory(layer__schema={
            'properties': {
                'logo': {
                    "type": "string",
                    "format": "data-url"
                }
            }
        })

    def test_render_view_not_found(self):
        feature = Feature.objects.create(geom=Point(0, 0, srid=4326),
                                         properties={"age": 10, "name": "jec", "country": "slovenija"},
                                         layer=self.crud_view.layer)
        response = self.client.get(reverse('terra_geocrud:render-file', args=(feature.pk, 'logo')))
        self.assertEqual(response.status_code, 404)

    def test_render_view_found(self):
        data_image = b64encode(b'test')
        feature = Feature.objects.create(geom=Point(0, 0, srid=4326),
                                         properties={"logo": f"data=image/png;name=avatar.png;base64,{data_image}"},
                                         layer=self.crud_view_file.layer)
        response = self.client.get(reverse('terra_geocrud:render-file', args=(feature.pk, 'logo')))
        self.assertEqual(response.status_code, 200)
