import base64
import mimetypes
from urllib.parse import unquote

from django.core.files.base import ContentFile
from django.core.files.storage import get_storage_class

from terra_geocrud import settings as app_settings

from sorl.thumbnail import delete


def get_info_content(value):
    """ Get splitted infos from base64 value. File info at first, then file content """
    if value:
        return value.split(';base64,')
    else:
        return None, None


def get_storage():
    """ Get media storage for feature data element, using settings """
    StorageClass = get_storage_class(import_path=app_settings.TERRA_GEOCRUD['DATA_FILE_STORAGE_CLASS'])
    return StorageClass()


def generate_storage_file_path(prop, value, feature):
    """ Generate final name to store file in storage """
    file_info, file_content = get_info_content(value)

    if file_info:
        # guess filename and extension
        infos = file_info.split(';') if file_info else ''
        try:
            # get name
            file_name = infos[1].split('=')[1]
        except IndexError:
            extension = mimetypes.guess_extension(infos[0].split(':')[1])
            file_name = f"{prop}{extension}"

        # some file_name can be uri encoded
        file_name = unquote(file_name)

        # build name in storage
        return f'terra_geocrud/features/{feature.pk}/data_file/{prop}/{file_name}'


def delete_old_picture_property(file_prop, old_properties):
    storage = get_storage()
    old_value = old_properties.get(file_prop)
    old_storage_file_path = old_value.split(';name=')[-1].split(';')[0] if old_value else None
    if old_storage_file_path:
        storage.delete(old_storage_file_path)
        delete(old_storage_file_path)


def get_files_properties(feature):
    files_properties = [
        key for key, value in feature.layer.schema['properties'].items()
        if feature.layer.schema['properties'][key].get('format') == 'data-url'
    ]
    return files_properties


def delete_feature_files(feature):
    files_properties = get_files_properties(feature)
    if files_properties:
        for file_prop in files_properties:
            delete_old_picture_property(file_prop, feature.properties)


def store_feature_files(feature, old_properties=None):
    """ Handle base64 encoded files to django storage. Use fake base64 to compatibility with react-json-schema """
    fake_content = 'R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs='
    files_properties = get_files_properties(feature)
    if files_properties:
        storage = get_storage()
        for file_prop in files_properties:
            value = feature.properties.get(file_prop)
            if value:
                storage_file_path = generate_storage_file_path(file_prop, value, feature)
                file_info, file_content = get_info_content(value)
                # check if file has been saved in storage
                if file_content != fake_content:
                    delete_old_picture_property(file_prop, old_properties)
                    storage.save(storage_file_path, ContentFile(base64.b64decode(file_content)))
                    # patch file_infos with new path
                    detail_infos = file_info.split(';name=')
                    new_info = f"{detail_infos[0]};name={storage_file_path}"
                    feature.properties[file_prop] = f'{new_info};base64,{fake_content}'
                    feature.save()


def get_storage_file_url(storage_file_path):
    # check if there is file in storage, else store it
    if storage_file_path:
        storage = get_storage()
        return storage.url(storage_file_path)


def get_storage_path_from_infos(infos):
    """ path is stored behind name= """
    file_infos = infos.split(';')
    return file_infos[1].split('name=')[-1]


def get_storage_path_from_value(value):
    infos, content = get_info_content(value)
    return get_storage_path_from_infos(infos)
