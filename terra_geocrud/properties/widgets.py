import inspect
import sys

from django.template.defaultfilters import date as date_filter
from django.utils.dateparse import parse_date
from django.utils.module_loading import import_string

from terra_geocrud.properties.files import get_storage_file_url


def render_property_data(feature, property_renderer):
    """ apply widget """
    widget_class = import_string(property_renderer.widget)
    widget = widget_class(feature=feature, prop=property_renderer.property, args=property_renderer.args)
    return widget.render()


def get_widgets_choices():
    """ List all widget available in choices format """
    widgets = []

    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if getattr(obj, 'widget', False):
            # get BaseWidget subclasses
            widgets.append((f"{__name__}.{name}", name))

    return widgets


class BaseWidget(object):
    """ Base widget. Inherit all widget from it, and override render method. """
    def __init__(self, feature, prop, args=None):
        if args is None:
            args = {}
        self.feature = feature
        self.property = prop
        self.args = args
        self.value = self.feature.properties.get(self.property)

    def render(self):
        raise NotImplementedError()


class DataUrlToImgWidget(BaseWidget):
    help = "Render img html tag with url to get b64 img stored in properties"
    widget = True

    def render(self):
        if self.value:
            attrs = self.args.get('attrs', {})
            final_attrs = ""
            for key, v in attrs.items():
                final_attrs += f' {key}="{v}"'
            url = get_storage_file_url(self.property, self.value, self.feature)
            return f'<img src="{url}" {final_attrs} />'


class FileAhrefWidget(BaseWidget):
    help = "Render html tag with url to download b64 file stored in properties. args: text (string, default 'Download'"
    widget = True

    def render(self):
        if self.value:
            # get html attrs
            attrs = self.args.get('attrs', {})
            # get text content
            text = self.args.get('text', 'Download')
            # set target="_blank" by default
            attrs.setdefault('target', '_blank')
            final_attrs = ""
            for key, v in attrs.items():
                final_attrs += f' {key}="{v}"'
            url = get_storage_file_url(self.property, self.value, self.feature)
            return f'<a href="{url}" {final_attrs}>{text}</a>'


class DateFormatWidget(BaseWidget):
    help = "Format date with given format. args: format (string, default to SHORT_DATE_FORMAT)"
    widget = True

    def render(self):
        if self.value:
            date_format = self.args.get('format', 'SHORT_DATE_FORMAT')
            return date_filter(parse_date(self.value), date_format)
