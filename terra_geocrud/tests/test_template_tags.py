import json
import os
from tempfile import TemporaryDirectory
from unittest import mock

from django.conf import settings
from django.contrib.gis.geos import GeometryCollection, LineString, Point
from django.core.files.base import ContentFile
from django.template import Context, Template
from django.template.base import FilterExpression, Parser
from django.template.exceptions import TemplateSyntaxError
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from terra_geocrud.tests.settings import PICTURES_PATH

from . import factories
from .settings import FEATURE_PROPERTIES, LAYER_SCHEMA, SMALL_PICTURE

from geostore.models import Feature, FeatureExtraGeom, LayerExtraGeom
from geostore import GeometryTypes

from mapbox_baselayer.models import BaseLayerTile, MapBaseLayer
from terra_geocrud.models import ExtraLayerStyle, CrudViewProperty, PropertyEnum
from terra_geocrud.templatetags.map_tags import MapImageLoaderURLODTNode, stored_image_base64
from terra_geocrud import settings as app_settings
from ..properties.schema import sync_layer_schema


class MapImageUrlLoaderTestCase(TestCase):
    def setUp(self):
        self.crud_view_line = factories.CrudViewFactory(name="Line", order=0,
                                                        layer__schema=LAYER_SCHEMA,
                                                        layer__geom_type=GeometryTypes.LineString)
        self.crud_view_point = factories.CrudViewFactory(name="Point", order=0,
                                                         layer__schema=LAYER_SCHEMA,
                                                         layer__geom_type=GeometryTypes.Point)

        self.line = Feature.objects.create(
            layer=self.crud_view_line.layer,
            geom=LineString((-0.246322800072846, 44.5562461167907), (0, 44)),
            properties=FEATURE_PROPERTIES,
        )
        self.point = Feature.objects.create(
            layer=self.crud_view_point.layer,
            geom=Point(x=-0.246322800072846, y=44.5562461167907),
            properties=FEATURE_PROPERTIES,
        )

        self.extra_layer = LayerExtraGeom.objects.create(layer=self.crud_view_line.layer, title='test')
        FeatureExtraGeom.objects.create(feature=self.point, layer_extra_geom=self.extra_layer,
                                        geom=Point((-0.5, 45.2)))
        FeatureExtraGeom.objects.create(feature=self.line, layer_extra_geom=self.extra_layer,
                                        geom=Point((-0.1, 44.2)))

        self.template = factories.TemplateDocxFactory.create(
            name='Template',
        )

        self.crud_view_point.templates.add(self.template)
        self.crud_view_line.templates.add(self.template)

        self.node = MapImageLoaderURLODTNode('http://mbglrenderer/render')

        self.token_mapbox = app_settings.TERRA_GEOCRUD.get('map', {}).get('mapbox_access_token')


@mock.patch('secrets.token_hex', side_effect=['primary', 'test'])
class StyleMapImageUrlLoaderTestCase(MapImageUrlLoaderTestCase):
    def test_get_style_default(self, token):
        self.maxDiff = None
        dict_style = {
            "version": 8,
            "sources":
                {"DEFAULT_MBGL_RENDERER_STYLE": {"type": "raster",
                                                 "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                                 "tileSize": 256,
                                                 "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "LineString", "coordinates": [[-0.246322800072846, 44.5562461167907],
                                                                            [0.0, 44.0]]}}},
            "layers": [
                {"id": "DEFAULT_MBGL_RENDERER_STYLE", "type": "raster", "source": "DEFAULT_MBGL_RENDERER_STYLE"},
                {"type": "line", "paint": {"line-color": "#000", "line-width": 3},
                 "id": "primary", "source": "primary"}]
        }
        self.assertDictEqual(dict_style, self.node.get_style(self.line, True, [''], None))

    def test_get_style_no_feature(self, token):
        self.maxDiff = None
        dict_style = {
            "version": 8,
            "sources":
                {"DEFAULT_MBGL_RENDERER_STYLE": {"type": "raster",
                                                 "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                                 "tileSize": 256,
                                                 "maxzoom": 18}},
            "layers": [
                {"id": "DEFAULT_MBGL_RENDERER_STYLE", "type": "raster", "source": "DEFAULT_MBGL_RENDERER_STYLE"}]
        }

        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, [''], None))

    def test_get_style_no_feature_extra_feature(self, token):
        self.maxDiff = None
        dict_style = {
            "version": 8,
            "sources":
                {"DEFAULT_MBGL_RENDERER_STYLE": {"type": "raster",
                                                 "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                                 "tileSize": 256,
                                                 "maxzoom": 18},
                 'primary': {"type": "geojson",
                             "data": {"type": "Point", "coordinates": [-0.1, 44.2]}}},
            "layers": [
                {"id": "DEFAULT_MBGL_RENDERER_STYLE", "type": "raster", "source": "DEFAULT_MBGL_RENDERER_STYLE"},
                {"type": "circle", "paint": {"circle-color": "#000", "circle-radius": 8},
                 "id": "primary", "source": "primary"}]
        }
        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, ['test'], None))

    def test_get_style_no_feature_extra_feature_custom_style(self, token):
        self.maxDiff = None
        custom_style = {"type": "circle", "paint": {"circle-color": "#fff", "circle-radius": 8}}
        ExtraLayerStyle.objects.create(layer_extra_geom=self.extra_layer, crud_view=self.crud_view_line,
                                       map_style=custom_style)
        dict_style = {
            "version": 8,
            "sources":
                {"DEFAULT_MBGL_RENDERER_STYLE": {"type": "raster",
                                                 "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                                 "tileSize": 256,
                                                 "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "Point", "coordinates": [-0.1, 44.2]}}},
            "layers": [
                {"id": "DEFAULT_MBGL_RENDERER_STYLE", "type": "raster", "source": "DEFAULT_MBGL_RENDERER_STYLE"},
                {"type": "circle", "paint": {"circle-color": "#fff", "circle-radius": 8},
                 "id": "primary", "source": "primary"}]
        }
        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, ['test'], None))

    def test_get_style_no_feature_from_baselayer(self, token):
        self.maxDiff = None
        layer = MapBaseLayer.objects.create(name="BaseLayerCustom", order=0, base_layer_type="raster")
        BaseLayerTile.objects.create(url="test.test", base_layer=layer)
        MapBaseLayer.objects.create(name="OtherLayerCustom", order=1, base_layer_type="raster")

        dict_style = {
            "version": 8,
            "sources": {
                "baselayercustom": {
                    "type": "raster",
                    "tiles": ["test.test"],
                    'attribution': '',
                    'tileSize': 512,
                    "minzoom": 0,
                    "maxzoom": 22,
                }
            },
            'glyphs': 'mapbox://fonts/mapbox/{fontstack}/{range}.pbf',
            "layers": [{
                "id": "baselayercustom-background",
                "type": "raster",
                "source": "baselayercustom"
            }]
        }

        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, [''], None))

    def test_get_style_chosen_baselayer(self, token):
        self.maxDiff = None
        MapBaseLayer.objects.create(name="BaseLayerCustom", order=0, base_layer_type="raster")
        layer = MapBaseLayer.objects.create(name="OtherLayerCustom", order=1, base_layer_type="raster")
        BaseLayerTile.objects.create(url="test.test", base_layer=layer)

        dict_style = {
            "version": 8,
            "sources": {
                "otherlayercustom": {
                    "type": "raster",
                    "attribution": "",
                    "tileSize": 512,
                    "tiles": ["test.test"],
                    "minzoom": 0,
                    "maxzoom": 22
                }
            },
            'glyphs': 'mapbox://fonts/mapbox/{fontstack}/{range}.pbf',
            "layers": [{
                "id": "otherlayercustom-background",
                "type": "raster",
                "source": "otherlayercustom"
            }]
        }

        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, [''], 'otherlayercustom'))

    @mock.patch('requests.get')
    def test_get_style_no_feature_from_mapbox_baselayer(self, mocked_get, token):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json.return_value = {"custom": "style"}
        self.maxDiff = None
        MapBaseLayer.objects.create(name="BaseLayerCustom", order=0, base_layer_type="mapbox", map_box_url="test.com")
        MapBaseLayer.objects.create(name="OtherLayerCustom", order=1, base_layer_type="raster")

        self.assertDictEqual({"custom": "style"}, self.node.get_style(self.line, False, [''], None))


@mock.patch('secrets.token_hex', side_effect=['primary', 'test'])
class ContextMapImageUrlLoaderTestCase(MapImageUrlLoaderTestCase):
    def test_get_value_context_line(self, token):
        self.maxDiff = None
        self.node = MapImageLoaderURLODTNode('http://mbglrenderer/render', data={'width': None,
                                                                                 'height': None,
                                                                                 'feature_included': None,
                                                                                 'extra_features': None,
                                                                                 'base_layer': None})
        style = self.node.get_data(Context({'object': self.line}))
        dict_style = {
            "version": 8,
            "sources":
                {"DEFAULT_MBGL_RENDERER_STYLE": {"type": "raster",
                                                 "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                                 "tileSize": 256,
                                                 "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "LineString", "coordinates": [[-0.246322800072846, 44.5562461167907],
                                                                            [0.0, 44.0]]}}},
            "layers": [
                {"id": "DEFAULT_MBGL_RENDERER_STYLE", "type": "raster", "source": "DEFAULT_MBGL_RENDERER_STYLE"},
                {"type": "line", "paint": {"line-color": "#000", "line-width": 3},
                 "id": "primary", "source": "primary"}]
        }
        dict_style_post = {'style': json.dumps(dict_style),
                           'center': [-0.12316140003642298, 44.27812305839535],
                           'zoom': 8,
                           'width': 1024,
                           'height': 512,
                           'token': self.token_mapbox}
        self.assertDictEqual(dict_style_post, style)

    def test_get_value_context_point(self, token):
        self.maxDiff = None
        settings_terra = app_settings.TERRA_GEOCRUD
        settings_terra['MAX_ZOOM'] = 20
        self.node = MapImageLoaderURLODTNode('http://mbglrenderer/render', data={'width': None,
                                                                                 'height': None,
                                                                                 'feature_included': None,
                                                                                 'extra_features': None,
                                                                                 'base_layer': None})

        with override_settings(TERRA_GEOCRUD=settings_terra):
            style = self.node.get_data(Context({'object': self.point}))
        dict_style = {
            "version": 8,
            "sources":
                {"DEFAULT_MBGL_RENDERER_STYLE": {"type": "raster",
                                                 "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                                 "tileSize": 256,
                                                 "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "Point", "coordinates": [-0.246322800072846, 44.5562461167907]}}},
            "layers": [
                {"id": "DEFAULT_MBGL_RENDERER_STYLE", "type": "raster", "source": "DEFAULT_MBGL_RENDERER_STYLE"},
                {"type": "circle", "paint": {"circle-color": "#000", "circle-radius": 8}, "id": "primary",
                 "source": "primary"}]
        }
        dict_style_post = {'style': json.dumps(dict_style),
                           'center': [-0.246322800072846, 44.5562461167907],
                           'zoom': app_settings.TERRA_GEOCRUD['MAX_ZOOM'],
                           'width': 1024,
                           'height': 512,
                           'token': self.token_mapbox}
        self.assertDictEqual(dict_style_post, style)

    def test_get_value_context_line_with_extra_features(self, token):
        self.maxDiff = None
        self.node = MapImageLoaderURLODTNode(
            'http://mbglrenderer/render',
            data={'width': None,
                  'height': None,
                  'feature_included': None,
                  'base_layer': None,
                  'extra_features': FilterExpression("'test'", Parser(''))}
        )
        style = self.node.get_data(Context({'object': self.line}))

        dict_style = {
            "version": 8,
            "sources":
                {"DEFAULT_MBGL_RENDERER_STYLE": {"type": "raster",
                                                 "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                                 "tileSize": 256,
                                                 "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "LineString", "coordinates": [[-0.246322800072846, 44.5562461167907],
                                                                            [0.0, 44.0]]}},
                 "test": {"type": "geojson",
                          "data": {"type": "Point", "coordinates": [-0.1, 44.2]}}},
            "layers": [
                {"id": "DEFAULT_MBGL_RENDERER_STYLE", "type": "raster", "source": "DEFAULT_MBGL_RENDERER_STYLE"},
                {"type": "circle", "paint": {"circle-color": "#000", "circle-radius": 8}, "id": "test",
                 "source": "test"},
                {"type": "line", "paint": {"line-color": "#000", "line-width": 3},
                 "id": "primary", "source": "primary"}]
        }
        dict_style_post = {'style': json.dumps(dict_style),
                           'center': [-0.12316140003642298, 44.27812305839535],
                           'zoom': 8,
                           'width': 1024,
                           'height': 512,
                           'token': self.token_mapbox}

        self.assertDictEqual(dict_style_post, style)

    @mock.patch('requests.get')
    def test_get_style_extra_layer_no_extra_feature(self, mocked_get, token):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json.return_value = {"custom": "style"}
        self.extra_layer.features.all().delete()
        self.maxDiff = None
        MapBaseLayer.objects.create(name="BaseLayerCustom", order=0, base_layer_type="mapbox", map_box_url="test.com")
        MapBaseLayer.objects.create(name="OtherLayerCustom", order=1, base_layer_type="raster")

        self.assertDictEqual({"custom": "style"}, self.node.get_style(self.line, False, ['test'], None))


@mock.patch('secrets.token_hex', side_effect=['primary', 'test'])
class RenderMapImageUrlLoaderODTTestCase(MapImageUrlLoaderTestCase):
    @mock.patch('requests.post')
    def test_image_url_loader_object(self, mocked_post, token):
        mocked_post.return_value.status_code = 200
        mocked_post.return_value.content = SMALL_PICTURE
        context = Context({'object': self.line})
        template_to_render = Template('{% load map_tags %}{% map_image_url_loader %}')

        rendered_template = template_to_render.render(context)
        self.assertEqual('<draw:frame draw:name="test.png" svg:width="15.0" svg:height="15.0" '
                         'text:anchor-type="paragraph" draw:z-index="37">'
                         '<draw:image xlink:href="Pictures/test.png" xlink:type="simple" xlink:show="embed" '
                         'xlink:actuate="onLoad" draw:mime-type="image/png" />'
                         '</draw:frame>', rendered_template)

    def test_map_image_url_loader_usage(self, token):
        with self.assertRaises(TemplateSyntaxError) as cm:
            Template('{% load map_tags %}{% map_image_url_loader wrong_key="test" %}')
        self.assertEqual('Usage: {% map_image_url_loader width="5000" height="5000" feature_included=False '
                         'extra_features="feature_1" base_layer="mapbaselayer_1" anchor="as-char" %}', str(cm.exception))

    def test_image_url_loader_no_object(self, token):
        context = Context({'object': self.line})
        template_to_render = Template('{% load map_tags %}{% map_image_url_loader feature_included=False %}')

        rendered_template = template_to_render.render(context)
        self.assertEqual('', rendered_template)


class RenderMapImageUrlLoaderPDFTestCase(MapImageUrlLoaderTestCase):
    @mock.patch('requests.post')
    def test_image_url_loader_object(self, mocked_post):
        mocked_post.return_value.status_code = 200
        mocked_post.return_value.content = SMALL_PICTURE
        context = Context({'object': self.line})
        template_to_render = Template('{% load map_tags %}{% image_base64_from_url %}')

        rendered_template = template_to_render.render(context)
        self.assertTrue(rendered_template.startswith("data:image/png;base64,"))
        self.assertTrue(rendered_template.endswith("="))

    def test_map_image_url_loader_usage(self):
        with self.assertRaises(TemplateSyntaxError) as cm:
            Template('{% load map_tags %}{% image_base64_from_url wrong_key="test" %}')
        self.assertEqual('Usage: {% image_base64_from_url width="5000" height="5000" feature_included=False '
                         'extra_features="feature_1" base_layer="mapbaselayer_1" %}', str(cm.exception))

    def test_image_url_loader_no_object(self):
        context = Context({'object': self.line})
        template_to_render = Template('{% load map_tags %}{% image_base64_from_url feature_included=False %}')

        rendered_template = template_to_render.render(context)
        self.assertEqual('', rendered_template)


class ZoomLineMapImageUrlLoaderTestCase(TestCase):
    def test_get_zoom(self):
        node = MapImageLoaderURLODTNode('http://mbglrenderer/render')
        collection = GeometryCollection(LineString([[-180, -85.06], [180, 85.06]]), srid=4326)
        self.assertEqual(0, node.get_zoom_bounds(1024, 1024, collection))

    def test_get_zoom_no_width(self):
        node = MapImageLoaderURLODTNode('http://mbglrenderer/render')
        collection = GeometryCollection(LineString([[0, -85.06], [0, 85.06]]), srid=4326)
        self.assertEqual(0, node.get_zoom_bounds(1024, 1024, collection))

    def test_get_zoom_no_height(self):
        node = MapImageLoaderURLODTNode('http://mbglrenderer/render')
        collection = GeometryCollection(LineString([[-180, 0], [180, 0]]), srid=4326)
        self.assertEqual(0, node.get_zoom_bounds(1024, 1024, collection))


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class StoredBase64FileTestCase(APITestCase):
    def setUp(self) -> None:
        self.crud_view = factories.CrudViewFactory()
        CrudViewProperty.objects.create(view=self.crud_view, key="logo",
                                        json_schema={'type': "string",
                                                     "title": "Logo",
                                                     "format": "data-url"})
        CrudViewProperty.objects.create(view=self.crud_view, key="no_value",
                                        json_schema={'type': "string",
                                                     "title": 'no_value',
                                                     "format": "data-url"})
        sync_layer_schema(self.crud_view)
        self.feature = Feature.objects.create(
            layer=self.crud_view.layer,
            geom="POINT(0 0)"
        )

        response = self.client.patch(reverse('feature-detail',
                                             args=(self.crud_view.layer_id,
                                                   self.feature.identifier)),
                                     data={"properties": {"logo": "data:image/png;name=titre_laromieu-fondblanc.jpg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}},
                                     format="json")
        self.assertEqual(response.status_code, 200, response.__dict__)

    def test_rendering(self):
        """ b64 data is in data rendering """
        self.feature.refresh_from_db()
        data = stored_image_base64(self.feature.properties['logo'])
        self.assertTrue(data.startswith("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9"))

    def test_wrong_rendering(self):
        """ rendering does work when document/pdf with data-url format"""
        response = self.client.patch(reverse('feature-detail',
                                             args=(self.crud_view.layer_id,
                                                   self.feature.identifier)),
                                     data={"properties": {"logo": "data;name=titre_laromieu-fondblanc.jpg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}},
                                     format="json")
        self.assertEqual(response.status_code, 200, response.__dict__)
        self.feature.refresh_from_db()
        data = stored_image_base64(self.feature.properties['logo'])
        self.assertTrue(data.startswith("data;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9"))


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class PictogramURLForValueTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.picture_name = 'small_picture.png'
        cls.crud_view = factories.CrudViewFactory()
        cls.property = CrudViewProperty.objects.create(view=cls.crud_view, key="gender",
                                                       json_schema={'type': "string",
                                                                    "title": "Gender", })
        CrudViewProperty.objects.create(view=cls.crud_view, key="other",
                                        json_schema={'type': "string",
                                                     "title": "Other", })
        with open(os.path.join(PICTURES_PATH, cls.picture_name), 'rb') as picto:
            PropertyEnum.objects.create(
                value="M",
                pictogram=ContentFile(picto.read(), name=cls.picture_name),
                property=cls.property
            )
        sync_layer_schema(cls.crud_view)
        cls.feature = Feature.objects.create(
            layer=cls.crud_view.layer,
            geom="POINT(0 0)",
            properties={
                "gender": "M"
            }
        )

    def test_rendering_with_picto(self):
        context = Context({'object': self.feature})
        template_to_render = Template('{% load map_tags %}{{ object|get_pictogram_url_for_value:"gender" }}')
        rendered_template = template_to_render.render(context)
        self.assertTrue(rendered_template.startswith(settings.MEDIA_URL))
        self.assertTrue(rendered_template.endswith(self.picture_name))

    def test_rendering_without_picto(self):
        context = Context({'object': self.feature})
        template_to_render = Template('{% load map_tags %}{{ object|get_pictogram_url_for_value:"other" }}')
        rendered_template = template_to_render.render(context)
        self.assertEqual(rendered_template, "")
