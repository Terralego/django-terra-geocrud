from . import settings as app_settings


def get_default_style(layer):
    style_settings = app_settings.TERRA_GEOCRUD.get('STYLES', {})
    if layer.is_point:
        response = style_settings.get('point')
    elif layer.is_linestring:
        response = style_settings.get('line')
    elif layer.is_polygon:
        response = style_settings.get('polygon')
    return response
