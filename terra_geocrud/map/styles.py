from ast import literal_eval
from copy import deepcopy

from django.utils.functional import cached_property

from terra_geocrud import settings as app_settings

DEFAULT_MBGL_RENDERER_STYLE = {
    'version': 8,
    'sources': {"DEFAULT_MBGL_RENDERER_STYLE": {
        "type": "raster",
        "tiles": ["http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
        "tileSize": 256,
        "maxzoom": 18}},
    'layers': [{
        'id': 'DEFAULT_MBGL_RENDERER_STYLE',
        "type": "raster",
        "source": "DEFAULT_MBGL_RENDERER_STYLE"}]
}

DEFAULT_STYLE_LINE = literal_eval(app_settings.DEFAULT_STYLE_LINE) \
    if isinstance(app_settings.DEFAULT_STYLE_LINE, str) \
    else app_settings.DEFAULT_STYLE_LINE
DEFAULT_STYLE_POINT = literal_eval(app_settings.DEFAULT_STYLE_POINT) \
    if isinstance(app_settings.DEFAULT_STYLE_POINT, str) \
    else app_settings.DEFAULT_STYLE_POINT
DEFAULT_STYLE_POLYGON = literal_eval(app_settings.DEFAULT_STYLE_POLYGON) \
    if isinstance(app_settings.DEFAULT_STYLE_POLYGON, str) \
    else app_settings.DEFAULT_STYLE_POLYGON


class MapStyleModelMixin:
    @cached_property
    def map_style_with_default(self):
        return deepcopy(self.map_style) if self.map_style else get_default_style(self.get_layer())


def get_default_style(layer):
    response = {}
    if layer.is_point:
        response = DEFAULT_STYLE_POINT
    elif layer.is_linestring:
        response = DEFAULT_STYLE_LINE
    elif layer.is_polygon:
        response = DEFAULT_STYLE_POLYGON
    return deepcopy(response)
