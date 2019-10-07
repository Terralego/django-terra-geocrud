import inspect
import sys

from rest_framework.reverse import reverse


def get_widgets_choices():
    """ List all widget available in choices format """
    widgets = []

    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if issubclass(obj, BaseWidget) and obj in BaseWidget.__subclasses__():
            # get BaseWidget subclasses
            widgets.append((f"{__name__}.{name}", name))

    return widgets


class BaseWidget(object):
    """ Base widget. Inherit all widget from it, and override render method. """
    def __init__(self, feature, property, args=None):
        if args is None:
            args = {}
        self.feature = feature
        self.property = property
        self.args = args
        self.value = self.feature.properties.get(self.property)

    def render(self, *args, **kwargs):
        raise NotImplementedError()


class DataUrlToImgWidget(BaseWidget):
    help = "Render img html tag with url to get b64 img stored in properties"

    def render(self, *args, **kwargs):
        if self.value:
            attrs = self.args
            final_attrs = ""
            for key, v in attrs.items():
                final_attrs += f' {key}="{v}"'
            url = reverse('terra_geocrud:render-file', args=(self.feature.pk,
                                                             self.property))
            return f'<img src="{url}" {final_attrs} />'


class FileAhrefWidget(BaseWidget):
    help = "Render a html tag with url to download b64 file stored in properties"

    def render(self, text="Download", **kwargs):
        if self.value:
            attrs = self.args
            # set target="_blank" by default
            attrs.setdefault('target', '_blank')
            final_attrs = ""
            for key, v in attrs.items():
                final_attrs += f' {key}="{v}"'
            url = reverse('terra_geocrud:render-file', args=(self.feature.pk,
                                                             self.property))
            return f'<a href="{url}" {final_attrs}>{text}</a>'
