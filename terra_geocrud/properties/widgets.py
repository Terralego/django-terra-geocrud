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
    def __init__(self, feature, property):
        self.feature = feature
        self.property = property
        self.value = self.feature.properties.get(self.property)

    def render(self, *args, **kwargs):
        raise NotImplementedError()


class DataUrlToImgWidget(BaseWidget):
    help = "Render img html tag with url to get b64 img stored in properties"

    def render(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        final_attrs = ""
        for key, v in attrs.items():
            final_attrs += f' {key}="{v}"'
        url = reverse('terra_geocrud:render-file', args=(self.feature.pk,
                                                         self.property))

        return f'<img src="{url}" {final_attrs} />'
