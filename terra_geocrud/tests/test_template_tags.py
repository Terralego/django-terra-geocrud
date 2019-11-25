import json
from unittest import mock

from django.contrib.gis.geos import LineString, Point
from django.template import Context, Template
from django.template.base import FilterExpression, Parser
from django.test import TestCase
from django.test.utils import override_settings

from . import factories
from .settings import FEATURE_PROPERTIES, LAYER_SCHEMA, SMALL_PICTURE

from geostore.models import Feature, FeatureExtraGeom, LayerExtraGeom
from geostore import GeometryTypes

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
        FeatureExtraGeom.objects.create(feature=self.line, layer_extra_geom=self.extra_layer,
                                        geom=Point((-0.1, 44.2)))

        self.template = factories.TemplateDocxFactory.create(
            name='Template',
        )

        self.crud_view_point.templates.add(self.template)
        self.crud_view_line.templates.add(self.template)

        self.node = MapImageLoaderNodeURL('http://mbglrenderer/render')

    def test_get_style_default(self):
        self.maxDiff = None
        dict_style = {
            "version": 8,
            "sources":
                {"TMP_MBGL_BASEMAP": {"type": "raster",
                                      "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                      "tileSize": 256,
                                      "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "LineString", "coordinates": [[-0.246322800072846, 44.5562461167907],
                                                                            [0.0, 44.0]]}}},
            "layers": [
                {"id": "TMP_MBGL_BASEMAP", "type": "raster", "source": "TMP_MBGL_BASEMAP"},
                {"type": "line", "paint": {"line-color": "#000", "line-width": 3},
                 "id": "primary", "source": "primary"}]
        }
        self.assertDictEqual(dict_style, self.node.get_style(self.line, True, ['']))

    def test_get_style_no_feature(self):
        self.maxDiff = None
        dict_style = {
            "version": 8,
            "sources":
                {"TMP_MBGL_BASEMAP": {"type": "raster",
                                      "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                      "tileSize": 256,
                                      "maxzoom": 18}},
            "layers": [
                {"id": "TMP_MBGL_BASEMAP", "type": "raster", "source": "TMP_MBGL_BASEMAP"}]
        }
        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, ['']))

    def test_get_style_no_feature_extra_feature(self):
        self.maxDiff = None
        dict_style = {
            "version": 8,
            "sources":
                {"TMP_MBGL_BASEMAP": {"type": "raster",
                                      "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                      "tileSize": 256,
                                      "maxzoom": 18},
                 self.extra_layer.name: {"type": "geojson",
                                         "data": {"type": "Point", "coordinates": [-0.1, 44.2]}}},
            "layers": [
                {"id": "TMP_MBGL_BASEMAP", "type": "raster", "source": "TMP_MBGL_BASEMAP"},
                {"type": "circle", "paint": {"circle-color": "#000", "circle-radius": 8},
                 "id": self.extra_layer.name, "source": self.extra_layer.name}]
        }
        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, ['test']))

    def test_get_style_no_feature_extra_feature_custom_style(self):
        self.maxDiff = None
        custom_style = {"type": "circle", "paint": {"circle-color": "#fff", "circle-radius": 8}}
        ExtraLayerStyle.objects.create(layer_extra_geom=self.extra_layer, crud_view=self.crud_view_line,
                                       map_style=custom_style)
        dict_style = {
            "version": 8,
            "sources":
                {"TMP_MBGL_BASEMAP": {"type": "raster",
                                      "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                      "tileSize": 256,
                                      "maxzoom": 18},
                 self.extra_layer.name: {"type": "geojson",
                                         "data": {"type": "Point", "coordinates": [-0.1, 44.2]}}},
            "layers": [
                {"id": "TMP_MBGL_BASEMAP", "type": "raster", "source": "TMP_MBGL_BASEMAP"},
                {"type": "circle", "paint": {"circle-color": "#fff", "circle-radius": 8},
                 "id": self.extra_layer.name, "source": self.extra_layer.name}]
        }
        self.assertDictEqual(dict_style, self.node.get_style(self.line, False, ['test']))

    def test_get_value_context_line(self):
        self.maxDiff = None
        self.node = MapImageLoaderNodeURL('http://mbglrenderer/render', data={'feature_included': None,
                                                                              'extra_features': None})
        style = self.node.get_data(Context({'object': self.line}))
        dict_style = {
            "version": 8,
            "sources":
                {"TMP_MBGL_BASEMAP": {"type": "raster",
                                      "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                      "tileSize": 256,
                                      "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "LineString", "coordinates": [[-0.246322800072846, 44.5562461167907],
                                                                            [0.0, 44.0]]}}},
            "layers": [
                {"id": "TMP_MBGL_BASEMAP", "type": "raster", "source": "TMP_MBGL_BASEMAP"},
                {"type": "line", "paint": {"line-color": "#000", "line-width": 3},
                 "id": "primary", "source": "primary"}]
        }
        dict_style_post = {'style': json.dumps(dict_style),
                           'bounds': '-0.246322800072846,44.0,0.0,44.5562461167907',
                           'width': 1024,
                           'height': 512,
                           'token': None}
        self.assertDictEqual(dict_style_post, style)

    def test_get_value_context_point(self):
        self.maxDiff = None
        settings_terra = app_settings.TERRA_GEOCRUD
        settings_terra['MAX_ZOOM'] = 20
        self.node = MapImageLoaderNodeURL('http://mbglrenderer/render', data={'feature_included': None,
                                                                              'extra_features': None})

        with override_settings(TERRA_GEOCRUD=settings_terra):
            style = self.node.get_data(Context({'object': self.point}))
        dict_style = {
            "version": 8,
            "sources":
                {"TMP_MBGL_BASEMAP": {"type": "raster",
                                      "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                      "tileSize": 256,
                                      "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "Point", "coordinates": [-0.246322800072846, 44.5562461167907]}}},
            "layers": [
                {"id": "TMP_MBGL_BASEMAP", "type": "raster", "source": "TMP_MBGL_BASEMAP"},
                {"type": "circle", "paint": {"circle-color": "#000", "circle-radius": 8}, "id": "primary",
                 "source": "primary"}]
        }
        dict_style_post = {'style': json.dumps(dict_style),
                           'center': [-0.246322800072846, 44.5562461167907],
                           'zoom': app_settings.TERRA_GEOCRUD['MAX_ZOOM'],
                           'width': 1024,
                           'height': 512,
                           'token': None}
        self.assertDictEqual(dict_style_post, style)

    def test_get_value_context_line_with_extra_features(self):
        self.maxDiff = None
        self.node = MapImageLoaderNodeURL('http://mbglrenderer/render', data={'feature_included': None,
                                                                              'extra_features': FilterExpression("'test'", Parser(''))})
        style = self.node.get_data(Context({'object': self.line}))

        dict_style = {
            "version": 8,
            "sources":
                {"TMP_MBGL_BASEMAP": {"type": "raster",
                                      "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                                      "tileSize": 256,
                                      "maxzoom": 18},
                 "primary": {"type": "geojson",
                             "data": {"type": "LineString", "coordinates": [[-0.246322800072846, 44.5562461167907],
                                                                            [0.0, 44.0]]}},
                 self.extra_layer.name: {"type": "geojson",
                                         "data": {"type": "Point", "coordinates": [-0.1, 44.2]}}},
            "layers": [
                {"id": "TMP_MBGL_BASEMAP", "type": "raster", "source": "TMP_MBGL_BASEMAP"},
                {"type": "circle", "paint": {"circle-color": "#000", "circle-radius": 8}, "id": self.extra_layer.name,
                 "source": self.extra_layer.name},
                {"type": "line", "paint": {"line-color": "#000", "line-width": 3},
                 "id": "primary", "source": "primary"}]
        }
        dict_style_post = {'style': json.dumps(dict_style),
                           'bounds': '-0.246322800072846,44.0,0.0,44.5562461167907',
                           'width': 1024,
                           'height': 512,
                           'token': None}

        self.assertDictEqual(dict_style_post, style)

    @mock.patch('secrets.token_hex', return_value='test')
    @mock.patch('requests.post')
    def test_image_url_loader_object(self, mocked_post, token):
        mocked_post.return_value.status_code = 200
        mocked_post.return_value.content = open(SMALL_PICTURE, 'rb').read()
        context = Context({'object': self.line})
        template_to_render = Template('{% load map_tags %}{% map_image_url_loader %}')

        rendered_template = template_to_render.render(context)
        self.assertEqual('<draw:frame draw:name="test" svg:width="16697.0" svg:height="16697.0" '
                         'text:anchor-type="paragraph" draw:z-index="0">'
                         '<draw:image xlink:href="Pictures/test" xlink:show="embed" xlink:actuate="onLoad"/>'
                         '</draw:frame>', rendered_template)

    @mock.patch('secrets.token_hex', return_value='test')
    @mock.patch('requests.post')
    def test_map_image_url_loader_usage(self, mocked_post, token):
        mocked_post.return_value.status_code = 200
        mocked_post.return_value.content = open(SMALL_PICTURE, 'rb').read()
        context = Context({'object': self.line})
        template_to_render = Template('{% load map_tags %}{% map_image_url_loader wrong_key="test" %}')

        rendered_template = template_to_render.render(context)
        self.assertEqual('<draw:frame draw:name="test" svg:width="16697.0" svg:height="16697.0" '
                         'text:anchor-type="paragraph" draw:z-index="0">'
                         '<draw:image xlink:href="Pictures/test" xlink:show="embed" xlink:actuate="onLoad"/>'
                         '</draw:frame>', rendered_template)
