import datetime
import os
import pathlib

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone


class TemplateCacheFile:
    root_directory = getattr(settings, 'ROOT_DIR_TEMPLATE_CACHE_FILE', '')

    def __init__(self, template, feature):
        self.template = template
        self.feature = feature

    @property
    def extension(self):
        if not hasattr(self, '_extension'):
            self._extension = pathlib.Path(self.template.template_file.name).suffix
        return self._extension

    @property
    def name(self):
        if not hasattr(self, '_name'):
            self._name = '{}_{}'.format(self.template.name, self.feature.identifier)
        return self._name

    @property
    def filename(self):
        if not hasattr(self, '_filename'):
            self._filename = os.path.join(
                self.root_directory,
                '{}{}'.format(self.name, self.extension)
            )
        return self._filename

    @property
    def updated_at(self):
        if not hasattr(self, '_updated_at'):
            try:
                self._updated_at = datetime.datetime.strptime(
                    default_storage.open(
                        os.path.join(
                            self.root_directory,
                            '{}_updated_at'.format(self.name)
                        )
                    ).read(),
                    '%Y-%m-%dT%H:%M:%S.%fZ')
            except FileNotFoundError:
                self._updated_at = None
        return self._updated_at

    @updated_at.setter
    def updated_at(self, v):
        self._updated_at = v

    @property
    def is_outdated(self):
        last_template_update = self.template.updated
        last_feature_update = self.feature.updated_at
        if (not self.updated_at
           or self.updated_at < last_template_update
           or self.updated_at < last_feature_update):
            return True
        return False

    def get(self):
        content = None
        if not self.is_outdated:
            content = default_storage.open(self.filename, 'rb').read()
        return content

    def set(self, content):
        with default_storage.open(self.filename, 'wb') as writer:
            writer.write(content)
        self.updated_at = timezone.now()
        with default_storage.open(os.path.join(
            self.root_directory,
            '{}_updated_at'.format(self.name)
        ), 'w') as writer:
            writer.write(self.updated_at.isoformat())
