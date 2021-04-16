from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import date

from terra_geocrud.properties.files import get_info_content, get_storage_path_from_infos, get_storage_file_url
from terra_geocrud.thumbnail_backends import ThumbnailDataFileBackend

thumbnail_backend = ThumbnailDataFileBackend()


def generate_thumbnail_from_image(value, data, data_type):
    # generate / get thumbnail for image
    if not value:
        return data, data_type
    try:
        # try to get file info from "data:image/png;xxxxxxxxxxxxx" data
        infos, content = get_info_content(value)
        storage_file_path = get_storage_path_from_infos(infos)
        data['url'] = get_storage_file_url(storage_file_path)

        if infos and infos.split(';')[0].split(':')[1].split('/')[0] == 'image':
            # apply special cases for images
            data_type = 'image'
            try:
                data.update({
                    "thumbnail": thumbnail_backend.get_thumbnail(storage_file_path,
                                                                 "500x500",
                                                                 upscale=False).url
                })
            except ValueError:
                pass
    except IndexError:
        pass
    return data, data_type


def get_data_url_date(value, data_format):
    if data_format == 'data-url':
        # apply special cases for files
        data_type = 'file'
        data = {"url": None}
        return generate_thumbnail_from_image(value, data, data_type)
    elif data_format == "date":
        data_type = 'date'
        try:
            value_date = datetime.strptime(str(value), "%Y-%m-%d").date()
            data = date(value_date, 'SHORT_DATE_FORMAT')
            return data, data_type
        except ValueError:
            pass
    return value, 'data'


def get_display_value(value, crud_property, value_type):
    picto = ''
    try:
        value_match = crud_property.values.get(value=value)
        if value_match.pictogram:
            picto = f'<img src="{value_match.pictogram.url}"/>'
    except ObjectDoesNotExist:
        pass
    if value_type == list or picto:
        value = f'<div class="icon-text">{picto}<span>{value}</span></div>'
    return value


def serialize_group_properties(feature, final_properties, editables_properties):
    properties = {}

    for key, value in final_properties.items():
        data_format = feature.layer.schema.get('properties', {}).get(key, {}).get('format')

        # if value associated for property match, and has picto, use it in <img> tag
        value = feature.properties.get(key)
        # find if associated property has explicit values
        value, data_type = get_data_url_date(value, data_format)

        crud_property = feature.layer.crud_view.properties.get(key=key)
        data = get_display_value(value, crud_property, str) if not isinstance(value, list) else [get_display_value(val, crud_property, list)for val in value]

        properties.update({key: {
            "display_value": data,
            "type": data_type,
            "title": feature.layer.get_property_title(key),
            "value": value,
            "schema": feature.layer.schema.get('properties', {}).get(key),
            "ui_schema": feature.layer.crud_view.ui_schema.get(key, {}),
            "editable": editables_properties[key]
        }})
    return properties
