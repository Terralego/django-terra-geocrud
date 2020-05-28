from datetime import datetime

from django.template.defaultfilters import date

from terra_geocrud.properties.files import get_info_content, get_storage_path_from_infos, get_storage_file_url
from terra_geocrud.thumbnail_backends import ThumbnailDataFileBackend

thumbnail_backend = ThumbnailDataFileBackend()


def serialize_group_properties(feature, final_properties):
    properties = {}

    for key, value in final_properties.items():
        data_type = 'data'
        data = value
        data_format = feature.layer.schema.get('properties', {}).get(key, {}).get('format')

        if data_format == 'data-url':
            # apply special cases for files
            data_type = 'file'
            data = {"url": None}
            if value:
                # generate / get thumbnail for image
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
        elif data_format == "date":
            data_type = 'date'
            try:
                value_date = datetime.strptime(str(value), "%Y-%m-%d").date()
                data = date(value_date, 'SHORT_DATE_FORMAT')
            except ValueError:
                pass

        properties.update({key: {
            "display_value": data,
            "type": data_type,
            "title": feature.layer.get_property_title(key),
            "value": feature.properties.get(key),
            "schema": feature.layer.schema.get('properties', {}).get(key),
            "ui_schema": feature.layer.crud_view.ui_schema.get(key, {})
        }})

    return properties
