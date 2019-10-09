import base64
import inspect
import mimetypes
import sys

from django.core.files.base import ContentFile
from django.core.files.storage import get_storage_class
from django.template.defaultfilters import date as date_filter
from django.utils.dateparse import parse_date

from terra_geocrud import settings as app_settings


def get_widgets_choices():
    """ List all widget available in choices format """
    widgets = []

    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if (issubclass(obj, BaseWidget) or issubclass(obj, BaseDataFileWidget)) and (
                obj in BaseWidget.__subclasses__() or obj in BaseDataFileWidget.__subclasses__()) and not isinstance(
                obj, BaseDataFileWidget):
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


class BaseDataFileWidget(BaseWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_info, self.file_content = self.get_info_content()

    def get_info_content(self):
        if self.value:
            return self.value.split(';base64,')
        else:
            return None, None

    def get_storage(self):
        StorageClass = get_storage_class(import_path=app_settings.TERRA_GEOCRUD['DATA_FILE_STORAGE_CLASS'])
        return StorageClass()

    def get_storage_file_path(self):
        if self.file_info:
            # guess filename and extension
            infos = self.file_info.split(';') if self.file_info else ''
            try:
                # get name
                file_name = infos[1].split('=')[1]
            except IndexError:
                extension = ''
                try:
                    extension = mimetypes.guess_extension(infos[0].split(':')[1])
                except IndexError:
                    pass
                file_name = f"{self.property}{extension}"

            # build name in storage
            return f'terra_geocrud/data_file/features/{self.feature.pk}/{self.property}/{file_name}'

    def get_storage_file_url(self):
        # check if there is file in storage, else store it
        storage = self.get_storage()

        storage_file_path = self.get_storage_file_path()
        if storage_file_path:
            if not storage.exists(storage_file_path):
                # create if not exists
                storage.save(storage_file_path, ContentFile(base64.b64decode(self.file_content)))

            return storage.url(storage_file_path)


class DataUrlToImgWidget(BaseDataFileWidget):
    help = "Render img html tag with url to get b64 img stored in properties"

    def render(self):
        if self.value:
            attrs = self.args.get('attrs', {})
            final_attrs = ""
            for key, v in attrs.items():
                final_attrs += f' {key}="{v}"'
            url = self.get_storage_file_url()
            return f'<img src="{url}" {final_attrs} />'


class FileAhrefWidget(BaseDataFileWidget):
    help = "Render html tag with url to download b64 file stored in properties. args: text (string, default 'Download'"

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
            url = self.get_storage_file_url()
            return f'<a href="{url}" {final_attrs}>{text}</a>'


class DateFormatWidget(BaseWidget):
    help = "Format date with given format. args: format (string, default to SHORT_DATE_FORMAT)"

    def render(self):
        if self.value:
            date_format = self.args.get('format', 'SHORT_DATE_FORMAT')
            return date_filter(parse_date(self.value), date_format)
