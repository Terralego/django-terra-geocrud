from tempfile import TemporaryDirectory

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from geostore.tests.factories import FeatureFactory

from terra_geocrud.properties.files import get_info_content, generate_storage_file_path, get_storage, \
    get_storage_path_from_value, store_feature_files
from terra_geocrud.tests import factories
from terra_geocrud.thumbnail_backends import ThumbnailDataFileBackend

thumbnail_backend = ThumbnailDataFileBackend()


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class StorageFunctionTestCase(APITestCase):
    def setUp(self) -> None:
        self.property_key = 'logo'
        self.feature_without_file_name = FeatureFactory(
            properties={
                self.property_key: 'data:image/png;base64,xxxxxxxxxxxxxxxxxxxxxxxxxx=='
            }
        )
        self.feature_without_file_data = FeatureFactory(
            properties={
                self.property_key: None
            }
        )
        self.crud_view = factories.CrudViewFactory(
            layer__schema={
                'properties': {
                    self.property_key: {
                        "type": "string",
                        "format": 'data-url',
                    }
                }
            }
        )

        self.feature_with_file_name = FeatureFactory(
            layer=self.crud_view.layer,
            properties={
                self.property_key: 'data:image/png;name=toto.png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkqAcAAIUAgUW0RjgAAAAASUVORK5CYII='
            }
        )

    def test_get_info_content_no_data(self):
        info, content = get_info_content(self.feature_without_file_data.properties[self.property_key])
        self.assertIsNone(info)
        self.assertIsNone(content)

    def test_get_info_content_no_file_name(self):
        value = self.feature_without_file_name.properties[self.property_key]
        info, content = get_info_content(self.feature_without_file_name.properties[self.property_key])
        path = generate_storage_file_path(self.property_key, value, self.feature_without_file_name)
        self.assertTrue(path.endswith(f'{self.property_key}.png'), path)

    def test_send_file(self):
        data = {
            "geom": "POINT(0 0)",
            "properties": {
                self.property_key: 'data:image/png;name=change.png;base64,xxxxxxxxxxxxxxxxxxxxxxxxxx=='
            }
        }
        store_feature_files(self.feature_with_file_name, {})
        storage = get_storage()
        old_property_value = self.feature_with_file_name.properties.get(self.property_key)
        old_storage_file_path = old_property_value.split(';name=')[-1].split(';')[0]
        old_thumbnail = thumbnail_backend.get_thumbnail(old_storage_file_path, "500x500", crop='noop', upscale=False)
        self.assertTrue(storage.exists(old_thumbnail.name))
        self.assertTrue(storage.exists(old_storage_file_path))
        response = self.client.put(
            reverse('feature-detail',
                    args=(self.feature_with_file_name.layer_id,
                          self.feature_with_file_name.identifier)),
            data=data,
            format="json")
        self.assertFalse(storage.exists(old_storage_file_path))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        storage_file_path = generate_storage_file_path(self.property_key,
                                                       data['properties'].get(self.property_key),
                                                       self.feature_with_file_name)
        self.assertTrue(storage.exists(storage_file_path))

    def test_get_storage_path_from_value(self):
        data = get_storage_path_from_value("test;name=file.jpg;base64,xxxxxxxxx")
        self.assertEqual(data, "file.jpg")
