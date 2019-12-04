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


class MapStyleModelMixin:
    @cached_property
    def map_style_with_default(self):
        response = get_default_style(self.get_layer())
        style = self.map_style
        return deepcopy(style) if style else response


def get_default_style(layer):
    style_settings = app_settings.TERRA_GEOCRUD.get('STYLES', {})
    response = {}
    if layer.is_point:
        response = style_settings.get('point')
    elif layer.is_linestring:
        response = style_settings.get('line')
    elif layer.is_polygon:
        response = style_settings.get('polygon')
    return deepcopy(response)
