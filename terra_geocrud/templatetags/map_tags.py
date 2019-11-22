from django import template
from json import dumps, loads
from template_engines.templatetags.odt_tags import ImageLoaderNodeURL
from template_engines.templatetags.utils import parse_tag


register = template.Library()


@register.filter(is_safe=True)
def filter_features(basic_style, args=()):
    style = loads(basic_style['style'])
    features = args.split(',')
    for feature in features:
        style["sources"].pop(feature, None)
    basic_style['style'] = dumps(style)
    return basic_style


class MapImageLoaderNodeURL(ImageLoaderNodeURL):
    def get_value_context(self, context):
        final_url, final_request, final_max_width, \
        final_max_height, final_anchor, final_data = super().get_value_context(context)
        print(final_data)
        print(context)
        return final_url, final_request, final_max_width, final_max_height, final_anchor, final_data


@register.tag
def map_image_url_loader(parser, token):
    """
    Replace a tag by an image from the url you specified.
    The necessary key is url
    - url : Url where you want to get your picture
    Other keys : data, max_width, max_height, request
    - data : Use it only with post request
    - max_width : Width of the picture rendered
    - max_heigth : Height of the picture rendered
    - request : Type of request, post or get. Get by default.
    - anchor : Type of anchor, paragraph, as-char, char, frame, page
    """
    tag_name, args, kwargs = parse_tag(token, parser)
    usage = '{{% {tag_name} [url] max_width="5000" max_height="5000" ' \
            'request="GET" data="{{"data": "example"}}" anchor="as-char" %}}'.format(tag_name=tag_name)
    if len(args) > 1 or not all(key in ['max_width', 'max_height', 'request', 'data', 'anchor'] for key in kwargs.keys()):
        raise template.TemplateSyntaxError("Usage: %s" % usage)
    return MapImageLoaderNodeURL(*args, **kwargs)
