import base64
import logging
import math
import secrets
from copy import deepcopy
from json import dumps, loads

import requests
from django import template
from django.contrib.gis.geos import GeometryCollection, Point
from geostore.models import LayerExtraGeom
from geostore.settings import INTERNAL_GEOMETRY_SRID
from mapbox_baselayer.models import MapBaseLayer
from template_engines.templatetags.odt_tags import ImageLoaderNodeURL
from template_engines.templatetags.utils import parse_tag

from terra_geocrud import settings as app_settings
from terra_geocrud.map.styles import DEFAULT_MBGL_RENDERER_STYLE, get_default_style
from terra_geocrud.properties.files import get_info_content, get_storage

logger = logging.getLogger(__name__)
register = template.Library()


class MapImageLoaderNodeURL(ImageLoaderNodeURL):
    def get_data(self, context):
        final_data = self.data

        width = 1024 if not final_data['width'] else final_data['width'].resolve(context)
        height = 512 if not final_data['height'] else final_data['height'].resolve(context)
        feature_included = True if not final_data['feature_included'] else final_data['feature_included'].resolve(context)
        extras_included = [] if not final_data['extra_features'] else final_data['extra_features'].resolve(
            context).split(',')
        base_layer = None if not final_data['base_layer'] else final_data['base_layer'].resolve(context)

        feature = context['object']
        style = self.get_style(feature, feature_included, extras_included, base_layer)
        token = app_settings.TERRA_GEOCRUD.get('map', {}).get('mapbox_access_token')
        final_style = {
            'style': dumps(style),
            'width': width,
            'height': height,
            'token': token
        }
        geoms = []
        if feature_included:
            geoms.append(feature.geom)

        for feat in feature.extra_geometries.filter(layer_extra_geom__slug__in=extras_included):
            geoms.append(feat.geom)
        collections = GeometryCollection(*geoms, srid=INTERNAL_GEOMETRY_SRID)
        if not collections:
            return final_style
        elif len(collections) == 1 and isinstance(collections[0], Point):
            final_style['zoom'] = app_settings.TERRA_GEOCRUD.get('MAX_ZOOM', 22)
            final_style['center'] = list(feature.geom.centroid)
        else:
            final_style['center'] = list(collections.centroid)
            zoom = self.get_zoom_bounds(width, height, collections)
            final_style['zoom'] = zoom

        return final_style

    def get_zoom_bounds(self, width, height, collection):
        collection = collection.transform('3857', clone=True)
        extent = collection.extent
        length_x = (extent[2] - extent[0])
        length_y = (extent[3] - extent[1])
        length_per_tile_width = 512 * length_x / width
        length_per_tile_height = 512 * length_y / height
        RADIUS = 6378137
        CIRCUM = 2 * math.pi * RADIUS
        # Max zoom in most of the maps is 22.
        zoom_width = 22
        zoom_height = 22
        if length_per_tile_width:
            zoom_width = math.log(CIRCUM / length_per_tile_width, 2)
        if length_per_tile_height:
            zoom_height = math.log(CIRCUM / length_per_tile_height, 2)
        return math.floor(min(zoom_width, zoom_height))

    def get_value_context(self, context):
        final_anchor = "paragraph" if not self.anchor else self.anchor.resolve(context)
        final_url = self.url
        final_request = self.request
        final_data = self.get_data(context)
        return final_url, final_request, None, None, final_anchor, final_data

    def get_style_base_layer(self, base_layer):
        try:
            map_base_layer = MapBaseLayer.objects.get(slug=base_layer)
        except MapBaseLayer.DoesNotExist:
            logger.warning(f"MapBaseLayer with slug '{base_layer}' was not found. Try to get another map base layer.")
            map_base_layer = MapBaseLayer.objects.first()

        if map_base_layer:
            if map_base_layer.base_layer_type == 'mapbox':
                response = requests.get(map_base_layer.map_box_url.replace("mapbox://styles",
                                                                           "https://api.mapbox.com/styles/v1"),
                                        params={"access_token": app_settings.TERRA_GEOCRUD.get('map', {}).get(
                                            'mapbox_access_token')})
                if response.status_code == 200:
                    return response.json()
            else:
                return map_base_layer.tilejson
        return deepcopy(DEFAULT_MBGL_RENDERER_STYLE)

    def get_style(self, feature, feature_included, extras_included, base_layer):
        style_map = self.get_style_base_layer(base_layer)
        view = feature.layer.crud_view
        primary_layer = {}
        if feature_included:
            geojson_id = secrets.token_hex(15)
            primary_layer = view.map_style_with_default
            primary_layer['id'] = geojson_id
            primary_layer['source'] = geojson_id
            style_map['sources'].update({geojson_id: {'type': 'geojson', 'data': loads(feature.geom.geojson)}})

        for layer_extra_geom in feature.layer.extra_geometries.filter(slug__in=extras_included):
            extra_feature = feature.extra_geometries.filter(layer_extra_geom=layer_extra_geom).first()
            if not extra_feature:
                continue

            # get final style
            try:
                extra_layer = layer_extra_geom.style.map_style_with_default
            except LayerExtraGeom.style.RelatedObjectDoesNotExist:
                extra_layer = get_default_style(layer_extra_geom)

            extra_id = secrets.token_hex(15)
            extra_layer['id'] = extra_id
            extra_layer['source'] = extra_id
            style_map['sources'].update({extra_id: {'type': 'geojson',
                                                    'data': loads(extra_feature.geom.geojson)}})
            style_map['layers'].append(extra_layer)

        if primary_layer:
            style_map['layers'].append(primary_layer)
        return style_map


@register.tag
def map_image_url_loader(parser, token):
    """
    Replace a tag by the map generated by mbglrenderer.
    Optional keys : data, max_width, max_height, request
    - feature_included : Primary feature will be shown
    - extra_features : List of the extra feature you wan to add on your map
    - width : Width of the picture rendered
    - heigth : Height of the picture rendered
    - anchor : Type of anchor, paragraph, as-char, char, frame, page
    """
    tag_name, args, kwargs = parse_tag(token, parser)
    usage = '{{% {tag_name} width="5000" height="5000" feature_included=False extra_features="feature_1" ' \
            'base_layer="mapbaselayer_1" anchor="as-char" %}}'.format(tag_name=tag_name)
    if not all(key in ['width', 'height', 'feature_included',
                       'extra_features', 'anchor', 'base_layer'] for key in kwargs.keys()):
        raise template.TemplateSyntaxError("Usage: %s" % usage)
    kwargs['request'] = 'POST'
    kwargs['data'] = {'feature_included': kwargs.pop('feature_included', None),
                      'extra_features': kwargs.pop('extra_features', None),
                      'width': kwargs.pop('width', None),
                      'height': kwargs.pop('height', None),
                      'base_layer': kwargs.pop('base_layer', None)}
    return MapImageLoaderNodeURL(f"{app_settings.TERRA_GEOCRUD['MBGLRENDERER_URL']}/render", **kwargs)


@register.filter
def stored_image_base64(value):
    """ As data-url file are stored in custom storage and not in b64, we need to prepare data to use """
    infos, content = get_info_content(value)
    infos = infos.split(';')
    data_type = infos[0]
    data_path = infos[1].strip('name=')
    storage = get_storage()
    file_bytes = storage.open(data_path, 'rb').read()
    file_b64 = base64.encodebytes(file_bytes)
    result = f"{data_type};base64," + file_b64.decode()
    return result
