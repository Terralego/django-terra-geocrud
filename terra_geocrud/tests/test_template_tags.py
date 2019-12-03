import json
from unittest import mock

from django.contrib.gis.geos import GeometryCollection, LineString, Point
from django.template import Context, Template
from django.template.base import FilterExpression, Parser
from django.template.exceptions import TemplateSyntaxError
from django.test import TestCase
from django.test.utils import override_settings

from . import factories
from .settings import FEATURE_PROPERTIES, LAYER_SCHEMA, SMALL_PICTURE

from geostore.models import Feature, FeatureExtraGeom, LayerExtraGeom
from geostore import GeometryTypes

from mapbox_baselayer.models import BaseLayerTile, MapBaseLayer
from terra_geocrud.models import ExtraLayerStyle
from terra_geocrud.templatetags.map_tags import MapImageLoaderNodeURL
from terra_geocrud import settings as app_settings


class MapImageUrlLoaderTestCase(TestCase):
    def setUp(self):
        self.crud_view_line = factories.CrudViewFactory(name="Line", order=0,
                                                        layer__schema=json.load(open(LAYER_SCHEMA)),
                                                        layer__geom_type=GeometryTypes.LineString)
        self.crud_view_point = factories.CrudViewFactory(name="Point", order=0,
                                                         layer__schema=json.load(open(LAYER_SCHEMA)),
                                                         layer__geom_type=GeometryTypes.Point)

        self.line = Feature.objects.create(
            layer=self.crud_view_line.layer,
            geom=LineString((-0.246322800072846, 44.5562461167907), (0, 44)),
            properties=json.load(open(FEATURE_PROPERTIES)),
        )
        self.point = Feature.objects.create(
            layer=self.crud_view_point.layer,
            geom=Point(x=-0.246322800072846, y=44.5562461167907),
            properties=json.load(open(FEATURE_PROPERTIES)),
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

        self.node = MapImageLoaderNodeURL('http://mbglrenderer/render')

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
            "sources":
                {"baselayercustom": {"type": "raster",
                                     "tiles": ["test.test"],
                                     'attribution': '',
                                     'tileSize': 512,
                                     "minzoom": 0,
                                     "maxzoom": 22, }},
            "layers": [
                {"id": "baselayercustom-background", "type": "raster", "source": "baselayercustom"}]
        }

        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, [''], None))

    def test_get_style_chosen_baselayer(self, token):
        self.maxDiff = None
        MapBaseLayer.objects.create(name="BaseLayerCustom", order=0, base_layer_type="raster")
        layer = MapBaseLayer.objects.create(name="OtherLayerCustom", order=1, base_layer_type="raster")
        BaseLayerTile.objects.create(url="test.test", base_layer=layer)

        dict_style = {
            "version": 8,
            "sources":
                {"otherlayercustom": {"type": "raster",
                                      "attribution": "",
                                      "tileSize": 512,
                                      "tiles": ["test.test"],
                                      "minzoom": 0,
                                      "maxzoom": 22}},
            "layers": [
                {"id": "otherlayercustom-background", "type": "raster", "source": "otherlayercustom"}]
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
        self.node = MapImageLoaderNodeURL('http://mbglrenderer/render', data={'width': None,
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
        self.node = MapImageLoaderNodeURL('http://mbglrenderer/render', data={'width': None,
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
        self.node = MapImageLoaderNodeURL('http://mbglrenderer/render', data={'width': None,
                                                                              'height': None,
                                                                              'feature_included': None,
                                                                              'base_layer': None,
                                                                              'extra_features': FilterExpression("'test'", Parser(''))})
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
class RenderMapImageUrlLoaderTestCase(MapImageUrlLoaderTestCase):
    @mock.patch('requests.post')
    def test_image_url_loader_object(self, mocked_post, token):
        mocked_post.return_value.status_code = 200
        mocked_post.return_value.content = open(SMALL_PICTURE, 'rb').read()
        context = Context({'object': self.line})
        template_to_render = Template('{% load map_tags %}{% map_image_url_loader %}')

        rendered_template = template_to_render.render(context)
        self.assertEqual('<draw:frame draw:name="test.png" svg:width="15.0" svg:height="15.0" '
                         'text:anchor-type="paragraph" draw:z-index="0">'
                         '<draw:image xlink:href="Pictures/test.png" xlink:show="embed" xlink:actuate="onLoad"/>'
                         '</draw:frame>', rendered_template)

    @mock.patch('requests.post')
    def test_map_image_url_loader_usage(self, mocked_post, token):
        with self.assertRaises(TemplateSyntaxError) as cm:
            Template('{% load map_tags %}{% map_image_url_loader wrong_key="test" %}')
        self.assertEqual('Usage: {% map_image_url_loader width="5000" height="5000" feature_included=False '
                         'extra_features="feature_1" base_layer="mapbaselayer_1" anchor="as-char" %}', str(cm.exception))

    def test_image_url_loader_no_object(self, token):
        context = Context({'object': self.line})
        template_to_render = Template('{% load map_tags %}{% map_image_url_loader feature_included=False %}')

        rendered_template = template_to_render.render(context)
        self.assertEqual('', rendered_template)


class ZoomLineMapImageUrlLoaderTestCase(TestCase):
    def test_get_zoom(self):
        node = MapImageLoaderNodeURL('http://mbglrenderer/render')
        collection = GeometryCollection(LineString([[-180, -85.06], [180, 85.06]]), srid=4326)
        self.assertEqual(0, node.get_zoom_bounds(1024, 1024, collection))

    def test_get_zoom_no_width(self):
        node = MapImageLoaderNodeURL('http://mbglrenderer/render')
        collection = GeometryCollection(LineString([[0, -85.06], [0, 85.06]]), srid=4326)
        self.assertEqual(0, node.get_zoom_bounds(1024, 1024, collection))

    def test_get_zoom_no_height(self):
        node = MapImageLoaderNodeURL('http://mbglrenderer/render')
        collection = GeometryCollection(LineString([[-180, 0], [180, 0]]), srid=4326)
        self.assertEqual(0, node.get_zoom_bounds(1024, 1024, collection))
