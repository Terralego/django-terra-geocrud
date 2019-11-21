from django import template
from json import dumps, loads

register = template.Library()


@register.filter(is_safe=True)
def filter_features(basic_style, args=()):
    style = loads(basic_style['style'])
    features = args.split(',')
    for feature in features:
        style["sources"].pop(feature, None)
    basic_style['style'] = dumps(style)
    return basic_style
