from tempfile import TemporaryDirectory
from unittest.mock import patch, PropertyMock

from django.contrib.gis.geos import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import tag, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from geostore import GeometryTypes
from geostore.models import Feature, LayerExtraGeom, FeatureExtraGeom, LayerRelation
from geostore.tests.factories import LayerFactory
from rest_framework import status
from rest_framework.test import APITestCase
from terra_geocrud.properties.schema import sync_layer_schema

from terra_geocrud.tests.factories import AttachmentCategoryFactory, UserFactory, RoutingSettingsFactory

from terra_geocrud.models import CrudViewProperty, PropertyEnum
from . import factories
from .settings import FEATURE_PROPERTIES, LAYER_SCHEMA
from .. import models, settings as app_settings
from ..properties.schema import sync_ui_schema


class CrudGroupViewSetTestCase(APITestCase):
    def setUp(self):
        self.group = models.CrudGroupView.objects.create(name="group", order=0)

    def test_list_endpoint(self):
        response = self.client.get(reverse('crudgroupview-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), models.CrudGroupView.objects.count())

        self.assertEqual(data[0]['id'], self.group.pk)

    def test_detail_endpoint(self):
        response = self.client.get(reverse('crudgroupview-detail', args=(self.group.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['id'], self.group.pk)


class CrudViewSetTestCase(APITestCase):
    def setUp(self):
        self.group_1 = models.CrudGroupView.objects.create(name="group 1", order=0)
        self.group_2 = models.CrudGroupView.objects.create(name="group 2", order=1)
        self.view_1 = factories.CrudViewFactory(name="View 1", order=0, group=self.group_1)
        self.view_2 = factories.CrudViewFactory(name="View 2", order=0, group=self.group_2)
        self.view_3 = factories.CrudViewFactory(name="View 3", order=1, group=self.group_2)
        self.extra_layer = LayerExtraGeom.objects.create(geom_type=GeometryTypes.MultiPolygon,
                                                         title='extra geom 1',
                                                         layer=self.view_1.layer)

    def test_list_endpoint(self):
        response = self.client.get(reverse('crudview-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), models.CrudView.objects.count())

        self.assertEqual(data[0]['id'], self.view_1.pk)

    def test_detail_endpoint(self):
        response = self.client.get(reverse('crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['id'], self.view_1.pk)

    def test_default_point_style(self):
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.Point)
        response = self.client.get(reverse('crudview-detail', args=(crud_view.pk,)))
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
        response = self.client.get(reverse('crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], custom_style)

    def test_default_line_style(self):
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.LineString)
        response = self.client.get(reverse('crudview-detail', args=(crud_view.pk,)))
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
        response = self.client.get(reverse('crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], custom_style)

    def test_default_polygon_style(self):
        crud_view = factories.CrudViewFactory(layer__geom_type=GeometryTypes.Polygon)
        response = self.client.get(reverse('crudview-detail', args=(crud_view.pk,)))
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
        response = self.client.get(reverse('crudview-detail', args=(crud_view.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['map_style'], custom_style)

    def test_original_ui_schema(self):
        response = self.client.get(reverse('crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(data['ui_schema'], self.view_1.ui_schema, data)

    def test_grouped_ui_schema(self):
        group_1 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.view_1, label='test')
        group_2 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.view_1, label='test2')
        CrudViewProperty.objects.create(view=self.view_1, key="name",
                                        group=group_2,
                                        json_schema={'type': "string", "title": "Name"},
                                        ui_schema={'ui:widget': 'textarea'})
        CrudViewProperty.objects.create(view=self.view_1, key="age",
                                        group=group_1,
                                        json_schema={'type': "integer", "title": "Age"})
        CrudViewProperty.objects.create(view=self.view_1, key="country",
                                        json_schema={'type': "string", "title": "Country"})
        sync_ui_schema(self.view_1)
        response = self.client.get(reverse('crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(
            data['ui_schema'],
            {'ui:order': ['test', 'test2', '*'],
             'test': {'ui:order': ['*']},
             'test2': {'ui:order': ['*'],
                       'name': {'ui:widget': 'textarea'}}}
        )
        group_1.delete()
        group_2.delete()

    def test_json_schema(self):
        prop_country = CrudViewProperty.objects.create(view=self.view_1, key="country",
                                                       json_schema={'type': "string", "title": "Country"})
        prop_themes = CrudViewProperty.objects.create(view=self.view_1, key="themes",
                                                      json_schema={'type': "array", "items": {"type": "string"}})
        PropertyEnum.objects.create(value="France", property=prop_country)
        PropertyEnum.objects.create(value="Spain", property=prop_country)
        PropertyEnum.objects.create(value="Theme 1", property=prop_themes)
        PropertyEnum.objects.create(value="Theme 2", property=prop_themes)
        sync_ui_schema(self.view_1)
        sync_layer_schema(self.view_1)
        response = self.client.get(reverse('crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertDictEqual(
            data['form_schema'],
            {'properties': {'country': {'enum': ['Spain', 'France'],
                                        'title': 'Country',
                                        'type': 'string'},
                            "themes": {"type": "array",
                                       "items": {
                                           "type": "string",
                                           "enum": ["Theme 2", "Theme 1"]
                                       }}},
             'required': []})

    def test_property_enum_are_casted(self):
        prop_1 = CrudViewProperty.objects.create(view=self.view_1, key="age2",
                                                 json_schema={'type': "integer", "title": "Age"})
        prop_2 = CrudViewProperty.objects.create(view=self.view_1, key="height2",
                                                 json_schema={'type': "number", "title": "Height"})
        PropertyEnum.objects.create(value="1", property=prop_1)
        PropertyEnum.objects.create(value="2", property=prop_1)
        PropertyEnum.objects.create(value="1.1", property=prop_2)
        PropertyEnum.objects.create(value="2", property=prop_2)
        sync_ui_schema(self.view_1)
        sync_layer_schema(self.view_1)
        response = self.client.get(reverse('crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertListEqual(sorted(data['form_schema']['properties']['age2']['enum']),
                             sorted([1, 2]))
        self.assertListEqual(sorted(data['form_schema']['properties']['height2']['enum']),
                             sorted([1.1, 2]))

    def test_routing_settings_crudview_detail(self):
        RoutingSettingsFactory.create(provider="mapbox", mapbox_transit="driving", crud_view=self.view_1)
        response = self.client.get(reverse('crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        routing_settings = data['routing_settings']

        self.assertEqual(routing_settings[0]['provider']['name'], "mapbox")
        self.assertEqual(routing_settings[0]['provider']['options']["transit"], 'driving')

    @tag('routing', "Only geostore routing")
    def test_routing_settings_geostorecrudview_detail(self):
        layer = LayerFactory.create(routable=True)
        RoutingSettingsFactory.create(provider="geostore", layer=layer, crud_view=self.view_1)
        response = self.client.get(reverse('crudview-detail', args=(self.view_1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        routing_settings = data['routing_settings']

        self.assertEqual(routing_settings[0]['provider']['name'], "geostore")
        self.assertEqual(routing_settings[0]['provider']['options']['url'], reverse('layer-route', args=[layer.pk]))

        response = self.client.post(reverse('layer-route', args=[layer.pk]), {'geom': 'SRID=2154;LINESTRING(0 0, 1 1)', })
        data = response.json()
        self.assertNotEqual(data, {'detail': 'Not found.'})


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class CrudSettingsViewTestCase(TestCase):
    def setUp(self):
        self.group_1 = models.CrudGroupView.objects.create(name="group 1", order=0)
        self.group_2 = models.CrudGroupView.objects.create(name="group 2", order=1)
        self.view_1 = factories.CrudViewFactory(name="View 1", order=0, group=self.group_1)

        CrudViewProperty.objects.create(view=self.view_1, key="test_property", table_order=54, required=False)

        self.view_2 = factories.CrudViewFactory(name="View 2", order=0, group=self.group_2)
        self.view_3 = factories.CrudViewFactory(name="View 3", order=1, group=self.group_2)
        self.response = self.client.get(reverse('crud-settings'))

    def test_endpoint_access(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_endpoint_menu(self):
        """
        Menu has 1 section per group, and 1 section for non grouped views
        """
        data = self.response.json()
        self.assertEqual(len(data['menu']), models.CrudGroupView.objects.count() + 1)
        self.assertEqual(data['menu'][0]['crud_views'][0]['feature_list_properties']['test_property']['table_order'], 54)


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class CrudRenderPointTemplateDetailViewTestCase(APITestCase):
    def setUp(self):
        self.crud_view = factories.CrudViewFactory(name="Composantes", order=0,
                                                   layer__schema=LAYER_SCHEMA,
                                                   layer__geom_type=GeometryTypes.Point)
        self.extra_layer = LayerExtraGeom.objects.create(geom_type=GeometryTypes.MultiPolygon,
                                                         title='extra geom 1',
                                                         layer=self.crud_view.layer)

        self.feature = Feature.objects.create(
            layer=self.crud_view.layer,
            geom=Point(x=-0.246322800072846, y=44.5562461167907),
            properties=FEATURE_PROPERTIES,
        )
        self.template_odt = factories.TemplateDocxFactory.create(
            name='Template ODT',
        )
        self.template_pdf = factories.TemplatePDFFactory.create(
            name='Template PDF',
        )
        self.crud_view.templates.add(self.template_odt)
        self.crud_view.templates.add(self.template_pdf)

    def test_template_rendering_odt(self):
        response = self.client.get(
            reverse(
                'feature-generate-template',
                args=(self.feature.layer.pk, self.feature.identifier, self.template_odt.pk)
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'],
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    def test_template_rendering_pdf(self):
        response = self.client.get(
            reverse(
                'feature-generate-template',
                args=(self.feature.layer.pk, self.feature.identifier, self.template_pdf.pk)
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'],
                         'application/pdf')


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class CrudLayerViewsSetTestCase(APITestCase):
    def setUp(self):
        self.crud_view = factories.CrudViewFactory()
        self.layer = LayerFactory.create()

    def test_list_endpoint(self):
        # Should show only crud_view
        response_list = self.client.get(reverse('layer-list'), format="json")
        data = response_list.json()
        self.assertEqual(len(data), 1)


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class CrudFeatureViewsSetTestCase(APITestCase):
    def setUp(self):
        self.crud_view = factories.CrudViewFactory()
        # add extra geometries to layer
        self.extra_layer_1 = LayerExtraGeom.objects.create(
            layer=self.crud_view.layer,
            geom_type=GeometryTypes.Point,
            title='Extra 1'
        )
        self.extra_layer_2 = LayerExtraGeom.objects.create(
            layer=self.crud_view.layer,
            geom_type=GeometryTypes.LineString,
            title='Extra 2'
        )
        self.group_1 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test')
        self.group_2 = models.FeaturePropertyDisplayGroup.objects.create(crud_view=self.crud_view, label='test2')

        CrudViewProperty.objects.create(view=self.crud_view, key="name",
                                        group=self.group_2,
                                        json_schema={'type': "string", "title": "Name"})
        CrudViewProperty.objects.create(view=self.crud_view, key="age",
                                        group=self.group_1,
                                        json_schema={'type': "integer", "title": "Age"})
        CrudViewProperty.objects.create(view=self.crud_view, key="country",
                                        json_schema={'type': "string", "title": "Country"})

        self.feature = Feature.objects.create(geom=Point(0, 0, srid=4326),
                                              properties={
                                                  "age": 10,
                                                  "name": "2012-01-01",
                                                  "country": "slovenija"},
                                              layer=self.crud_view.layer)
        # add extra geometries to feature
        self.extra_feature = FeatureExtraGeom.objects.create(
            feature=self.feature,
            layer_extra_geom=self.extra_layer_1,
            geom='POINT(0 0)'
        )
        self.pictures = factories.FeaturePictureFactory.create_batch(10, feature=self.feature)
        self.attachments = factories.FeatureAttachmentFactory.create_batch(10, feature=self.feature)
        self.template = factories.TemplateDocxFactory()
        self.crud_view.templates.add(self.template)
        self.user = UserFactory()
        self.client.force_authenticate(self.user)

    def test_list_endpoint(self):
        response_list = self.client.get(reverse('feature-list', args=(self.crud_view.layer_id,)),
                                        format="json")
        data = response_list.json()
        features = self.crud_view.layer.features.all()
        self.assertEqual(len(data), len(features))

    def test_property_detail_display_with_groups(self):
        response_detail = self.client.get(reverse('feature-detail',
                                                  args=(self.crud_view.layer_id,
                                                        self.feature.identifier)),
                                          format="json")
        data = response_detail.json()
        expected_keys = list(self.crud_view.feature_display_groups.all()
                             .values_list('slug', flat=True)) + ['__default__']
        self.assertEqual(list(data['display_properties'].keys()), expected_keys)

    def test_property_detail_documents(self):
        response_detail = self.client.get(reverse('feature-detail',
                                                  args=(self.crud_view.layer_id,
                                                        self.feature.identifier)),
                                          format="json")
        data = response_detail.json()
        self.assertEqual(len(data['documents']), self.crud_view.templates.count())

    def test_create_grouped_properties(self):
        """ Test creation with grouped properties """
        data = {"geom": "POINT(0 0)",
                "properties": {
                    "test2": {"name": "toto"},
                    "test": {"age": 10},
                    "country": "France"
                }}

        response = self.client.post(reverse('feature-list',
                                            args=(self.crud_view.layer_id, )),
                                    data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        json_data = response.json()

        # feature properties are grouped in api
        self.assertDictEqual(json_data['properties'], data['properties'])

        # feature properties are not grouped in object
        feature = Feature.objects.get(pk=json_data['id'])
        self.assertDictEqual(feature.properties, {"name": "toto",
                                                  "age": 10,
                                                  "country": "France"})

    def test_attachment_endpoint(self):
        response = self.client.get(reverse('attachment-list',
                                           args=(self.feature.identifier, )))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_picture_endpoint(self):
        response = self.client.get(reverse('picture-list',
                                           args=(self.feature.identifier, )))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock)
    def test_featurerelation_without_crud_view(self, mocked):
        mocked.return_value = True
        layer_destination = LayerFactory.create()
        feature_destination = Feature.objects.create(geom=Point(0, 0, srid=4326), layer=layer_destination)
        intersect_relation = LayerRelation.objects.create(
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=layer_destination,
            settings={"distance": 100}
        )
        self.feature.sync_relations(intersect_relation.pk)
        response = self.client.get(reverse('feature-relation', args=(self.crud_view.layer_id,
                                                                     self.feature.identifier,
                                                                     intersect_relation.pk)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['identifier'], str(feature_destination.identifier))

    @patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock)
    def test_featurerelation_geojson(self, mocked):
        mocked.return_value = True
        crud_view = factories.CrudViewFactory()
        feature_destination = Feature.objects.create(geom=Point(0, 0, srid=4326), layer=crud_view.layer)
        intersect_relation = LayerRelation.objects.create(
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=crud_view.layer,
            settings={"distance": 100}
        )
        self.feature.sync_relations(intersect_relation.pk)
        response = self.client.get(reverse('feature-relation', args=(self.crud_view.layer_id,
                                                                     self.feature.identifier,
                                                                     intersect_relation.pk)),
                                   data={"format": "geojson"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['features'][0]['properties']['identifier'],
                         str(feature_destination.identifier))

    @patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock)
    def test_relations_featurelist_crud_view_do_not_show(self, mocked):
        mocked.return_value = True
        layer_destination = LayerFactory.create()
        crud_view = factories.CrudViewFactory()
        LayerRelation.objects.create(
            name='layer_view',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=layer_destination,
            settings={"distance": 100}
        )
        layer_rel = LayerRelation.objects.create(
            name='view_view',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=crud_view.layer,
            settings={"distance": 100}
        )
        response = self.client.get(reverse('feature-list', args=(self.crud_view.layer_id, )), data={}, format="json")
        url_relation = reverse('feature-relation', args=(self.crud_view.layer_id,
                                                         self.feature.identifier,
                                                         layer_rel.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['relations']['view_view'], url_relation)
        self.assertEqual(len(response.json()[0]['relations']), 1)

    @patch('geostore.settings.GEOSTORE_RELATION_CELERY_ASYNC', new_callable=PropertyMock)
    def test_relations_featuredetail_crud_view_do_not_show(self, mocked):
        mocked.return_value = True
        layer_destination = LayerFactory.create()
        crud_view = factories.CrudViewFactory()
        LayerRelation.objects.create(
            name='layer_view',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=layer_destination,
            settings={"distance": 100}
        )
        layer_rel = LayerRelation.objects.create(
            name='view_view',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=crud_view.layer,
            settings={"distance": 100}
        )
        response = self.client.get(reverse('feature-detail',
                                           args=(self.crud_view.layer_id,
                                                 self.feature.identifier)),
                                   format="json")
        url_relation = reverse('feature-relation', args=(self.crud_view.layer_id,
                                                         self.feature.identifier,
                                                         layer_rel.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['relations'][0]['label'], "view_view")
        self.assertEqual(response.json()['relations'][0]['url'], url_relation)
        self.assertEqual(response.json()['relations'][0]['empty'], True)
        self.assertEqual(len(response.json()['relations']), 1)
        Feature.objects.create(geom=Point(0, 0, srid=4326), layer=crud_view.layer)
        self.feature.sync_relations(layer_rel.pk)
        response = self.client.get(reverse('feature-detail',
                                           args=(self.crud_view.layer_id,
                                                 self.feature.identifier)),
                                   format="json")
        self.assertEqual(response.json()['relations'][0]['empty'], False)

    def test_relations_featuredetail_without_celery(self):
        crud_view = factories.CrudViewFactory()
        layer_rel = LayerRelation.objects.create(
            name='view_view',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=crud_view.layer,
            settings={"distance": 100}
        )
        response = self.client.get(reverse('feature-detail',
                                           args=(self.crud_view.layer_id,
                                                 self.feature.identifier)),
                                   format="json")
        url_relation = reverse('feature-relation', args=(self.crud_view.layer_id,
                                                         self.feature.identifier,
                                                         layer_rel.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['relations'][0]['label'], "view_view")
        self.assertEqual(response.json()['relations'][0]['url'], url_relation)
        self.assertEqual(len(response.json()['relations']), 1)

    def test_relations_featurelist_without_celery(self):
        crud_view = factories.CrudViewFactory()
        layer_rel = LayerRelation.objects.create(
            name='view_view',
            relation_type='distance',
            origin=self.crud_view.layer,
            destination=crud_view.layer,
            settings={"distance": 100}
        )
        response = self.client.get(reverse('feature-list', args=(self.crud_view.layer_id, )), data={}, format="json")
        url_relation = reverse('feature-relation', args=(self.crud_view.layer_id,
                                                         self.feature.identifier,
                                                         layer_rel.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['relations']['view_view'], url_relation)
        self.assertEqual(len(response.json()[0]['relations']), 1)

    def test_relations_featurelist_no_crud_view_boths(self):
        layer_destination = LayerFactory.create()
        layer_origin = LayerFactory.create()
        LayerRelation.objects.create(
            name='layer_layer',
            relation_type='distance',
            origin=layer_origin,
            destination=layer_destination,
            settings={"distance": 100}
        )
        response = self.client.get(reverse('feature-list', args=(self.crud_view.layer_id, )), data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()[0]['relations']), 0)

    def test_relations_featuredetail_no_crud_view_boths(self):
        layer_destination = LayerFactory.create()
        layer_origin = LayerFactory.create()
        LayerRelation.objects.create(
            name='layer_layer',
            relation_type='distance',
            origin=layer_origin,
            destination=layer_destination,
            settings={"distance": 100}
        )
        response = self.client.get(reverse('feature-detail',
                                           args=(self.crud_view.layer_id,
                                                 self.feature.identifier)),
                                   format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['relations']), 0)

    def test_route_description_featuredetail(self):
        data = {
            "routing_information": {"whatever": ["whatever"]},
            "geom": "POINT(0 1)"
        }
        response = self.client.patch(reverse('feature-detail',
                                             args=(self.crud_view.layer_id,
                                                   self.feature.identifier)),
                                     data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertEqual(json_response['routing_information'], {"whatever": ["whatever"]})
        self.assertEqual(json_response['geom'], {'type': 'Point', 'coordinates': [0.0, 1.0]})

        response = self.client.get(reverse('feature-detail',
                                           args=(self.crud_view.layer_id,
                                                 self.feature.identifier)),
                                   format="json")


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class FeatureAttachmentViewsetTesCase(APITestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        self.feature = Feature.objects.create(layer=self.crud_view.layer,
                                              geom='POINT(0 0)')
        self.category = AttachmentCategoryFactory()
        self.user = UserFactory()
        self.client.force_authenticate(self.user)

    def test_feature_is_not_required_in_attachment_creation(self):
        file = SimpleUploadedFile("file.jpg", b"file_content", content_type="image/jpg")
        response = self.client.post(reverse('attachment-list',
                                            args=(self.feature.identifier, )),
                                    {"category": self.category.pk,
                                     "legend": "file_test",
                                     "file": file}, format='multipart')
        self.assertEqual(response.status_code, 201, response.json())
