import json
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path

from django.template.defaultfilters import date
from django.utils.translation import gettext_lazy as _
from geostore.models import LayerExtraGeom
from geostore.serializers import LayerSerializer, FeatureSerializer, FeatureExtraGeomSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis import serializers as geo_serializers
from template_model.models import Template

from . import models
from .map.styles import get_default_style
from .properties.files import get_info_content, get_storage_file_url, \
    get_storage_path_from_infos, store_feature_files
from .thumbnail_backends import ThumbnailDataFileBackend


thumbnail_backend = ThumbnailDataFileBackend()


class BaseUpdatableMixin(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    def get_created_at(self, obj):
        return date(obj.created_at, 'SHORT_DATETIME_FORMAT')

    def get_updated_at(self, obj):
        return date(obj.updated_at, 'SHORT_DATETIME_FORMAT')


class LayerViewSerializer(LayerSerializer):
    schema = serializers.JSONField(write_only=True)
    # disable other fields
    name = serializers.CharField(read_only=True)
    layer_groups = None
    routing_url = None
    shapefile_url = None
    geojson_url = None
    layer_intersects = None

    class Meta(LayerSerializer.Meta):
        pass


class CrudViewSerializer(serializers.ModelSerializer):
    layer = LayerViewSerializer()
    object_name = serializers.SerializerMethodField()
    object_name_plural = serializers.SerializerMethodField()
    extent = serializers.SerializerMethodField()
    exports = serializers.SerializerMethodField()
    ui_schema = serializers.JSONField(source='grouped_ui_schema')
    form_schema = serializers.JSONField(source='grouped_form_schema')
    map_style = serializers.JSONField(source='map_style_with_default')
    map_layers = serializers.SerializerMethodField(help_text=_("VT styles and definitions"))
    feature_endpoint = serializers.SerializerMethodField(
        help_text=_("Url endpoint for view's features")
    )
    feature_list_properties = serializers.SerializerMethodField(
        help_text=_("Available properties for feature datatable. Ordered, {name: {title, type}}")
    )

    def get_object_name(self, obj):
        return obj.object_name if obj.object_name else obj.name

    def get_object_name_plural(self, obj):
        return obj.object_name_plural if obj.object_name_plural else obj.name

    def get_map_layers(self, obj):
        data = [{
            'title': obj.name,
            'id_layer_vt': obj.layer.name,
            'style': obj.map_style_with_default,
            'main': True
        }]
        # add extra_layer styles
        for extra_layer in obj.layer.extra_geometries.all():
            # get final style
            try:
                style = extra_layer.style.map_style_with_default
            except LayerExtraGeom.style.RelatedObjectDoesNotExist:
                style = get_default_style(extra_layer)

            data.append({
                'title': extra_layer.title,
                'id_layer_vt': extra_layer.name,
                'style': style,
                'main': False
            })
        return data

    def get_exports(self, obj):
        return [{
            "name": "shapefile",
            "url": reverse('layer-shapefile', args=[obj.layer_id, ])
        }, {
            "name": "geojson",
            "url": reverse('feature-list', kwargs={'layer': obj.layer_id, 'format': 'geojson'})
        }]

    def get_extent(self, obj):
        # TODO: use annotated extent
        return obj.extent

    def get_feature_list_properties(self, obj):
        # TODO: keep default properties at first, then order by property title
        default_list = list(obj.default_list_properties or obj.list_available_properties[:8])
        result = {
            prop: {
                "title": obj.layer.get_property_title(prop),
                "selected": True if prop in default_list else False,
                "type": obj.layer.get_property_type(prop)
            }
            for prop in obj.list_available_properties
        }
        # order by title
        return OrderedDict(sorted(result.items(), key=lambda x: x[1]['title']))

    def get_feature_endpoint(self, obj):
        return reverse('feature-list', args=(obj.layer_id,))

    class Meta:
        model = models.CrudView
        fields = (
            'id', 'name', 'object_name', 'object_name_plural',
            'pictogram', 'order', 'map_style',
            'form_schema', 'ui_schema', 'settings', 'layer',
            'feature_endpoint', 'extent', 'exports',
            'feature_list_properties', 'map_layers'
        )


class CrudGroupSerializer(serializers.ModelSerializer):
    crud_views = CrudViewSerializer(many=True, read_only=True)

    class Meta:
        model = models.CrudGroupView
        fields = '__all__'


class FeatureDisplayPropertyGroup(serializers.ModelSerializer):
    title = serializers.CharField(source='label')
    order = serializers.IntegerField()
    pictogram = serializers.ImageField()
    properties = serializers.SerializerMethodField()

    def get_properties(self, obj):
        """ Get feature properties in group to form { title: rendering(value) } """
        feature = self.context.get('feature')
        final_properties = {
            prop: feature.properties.get(prop)
            for prop in list(obj.properties)
        }

        properties = {}

        for key, value in final_properties.items():
            data_type = 'data'
            data = value
            data_format = feature.layer.schema.get('properties').get(key, {}).get('format')

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
                data = value

            properties.update({key: {
                "display_value": data,
                "type": data_type,
                "title": feature.layer.get_property_title(key),
                "value": feature.properties.get(key),
                "schema": feature.layer.schema.get('properties').get(key),
                "ui_schema": feature.layer.crud_view.ui_schema.get(key, {})
            }})

        return properties

    class Meta:
        model = models.FeaturePropertyDisplayGroup
        fields = ('title', 'slug', 'order', 'pictogram', 'properties')


class CrudFeatureListSerializer(BaseUpdatableMixin, FeatureSerializer):
    geom = None
    detail_url = serializers.SerializerMethodField()
    extent = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    def get_properties(self, obj):
        """ Keep only properties that can be shown in list """
        list_available_properties = list(obj.layer.crud_view.list_available_properties)
        return {
            key: value for key, value in obj.properties.items() if key in list_available_properties
        }

    def get_extent(self, obj):
        geom = obj.geom.transform(4326, clone=True)
        return geom.extent

    def get_detail_url(self, obj):
        return reverse('feature-detail',
                       args=(obj.layer_id, obj.identifier))

    class Meta(FeatureSerializer.Meta):
        exclude = ('source', 'target', 'layer', 'geom')
        fields = None


class DocumentFeatureSerializer(serializers.ModelSerializer):
    extension = serializers.SerializerMethodField()
    template_name = serializers.CharField(source='name')
    template_file = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    def get_extension(self, obj):
        return Path(obj.template_file.name).suffix

    def get_template_file(self, obj):
        return Path(obj.template_file.name).name

    def get_download_url(self, obj):
        return reverse('render-template',
                       args=(obj.pk, self.context.get('feature').pk))

    class Meta:
        fields = (
            'extension', 'template_name', 'template_file', 'download_url'
        )
        model = Template


class FeaturePictureSerializer(BaseUpdatableMixin):
    thumbnail = serializers.ImageField(read_only=True)
    action_url = serializers.SerializerMethodField()

    def get_action_url(self, obj):
        return reverse('picture-detail', args=(obj.feature.identifier,
                                               obj.pk, ))

    class Meta:
        model = models.FeaturePicture
        extra_kwargs = {
        }
        fields = ('id', 'category', 'legend', 'image', 'thumbnail', 'action_url', 'created_at', 'updated_at')


class FeatureAttachmentSerializer(BaseUpdatableMixin):
    action_url = serializers.SerializerMethodField()

    def get_action_url(self, obj):
        return reverse('attachment-detail', args=(obj.feature.identifier,
                                                  obj.pk, ))

    class Meta:
        model = models.FeatureAttachment
        fields = ('id', 'category', 'legend', 'file', 'action_url', 'created_at', 'updated_at')


class AttachmentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AttachmentCategory
        fields = '__all__'


class CrudFeatureDetailSerializer(BaseUpdatableMixin, FeatureSerializer):
    title = serializers.SerializerMethodField()
    geom = geo_serializers.GeometryField()
    documents = serializers.SerializerMethodField()
    display_properties = serializers.SerializerMethodField()
    properties = serializers.JSONField()
    attachments = serializers.SerializerMethodField()
    pictures = serializers.SerializerMethodField()
    geometries = serializers.SerializerMethodField()

    def get_pictures(self, obj):
        """ Return feature linked pictures grouped by category, with urls to create / replace / delete """
        return [{
            "name": category.name,
            "pictogram": category.pictogram.url if category.pictogram else None,
            "pictures": FeaturePictureSerializer(obj.pictures.filter(category=category),
                                                 many=True).data,
            "action_url": reverse('picture-list', args=(obj.identifier, ))
        } for category in models.AttachmentCategory.objects.all()]

    def get_attachments(self, obj):
        """ Return feature linked pictures grouped by category, with urls to create / replace / delete """
        return [{
            "name": category.name,
            "pictogram": category.pictogram.url if category.pictogram else None,
            "attachments": FeatureAttachmentSerializer(obj.attachments.filter(category=category),
                                                       many=True).data,
            "action_url": reverse('attachment-list', args=(obj.identifier, ))
        } for category in models.AttachmentCategory.objects.all()]

    def get_title(self, obj):
        """ Get Feature title, as feature_title_property content or identifier by default """
        return obj.layer.crud_view.get_feature_title(obj)

    def get_properties(self, obj):
        """ Feature properties as form initial data format (name / value) """
        results = {}
        crud_view = obj.layer.crud_view
        groups = crud_view.feature_display_groups.all()
        original_properties = deepcopy(obj.properties)

        # get ordered groups filled
        for group in groups:
            results[group.slug] = {}
            for prop in group.properties:
                results[group.slug][prop] = original_properties.pop(prop, None)

        return {**results, **original_properties}

    def get_display_properties(self, obj):
        """ Feature properties to display (key / value, display value and info) """
        processed_properties = []
        results = {}
        crud_view = obj.layer.crud_view
        groups = crud_view.feature_display_groups.all()

        # get ordered groups filled
        for group in groups:
            serializer = FeatureDisplayPropertyGroup(group,
                                                     context={'request': self.context.get('request'),
                                                              'feature': obj})
            results[group.slug] = serializer.data
            processed_properties += list(group.properties)

        # add default other properties
        remained_properties = list(set(crud_view.properties) - set(processed_properties))
        if remained_properties:
            # reconstruct property key/value list based on layer schema
            final_properties = {
                prop: obj.properties.get(prop)
                for prop in list(remained_properties)
            }
            properties = {}

            for key, value in final_properties.items():
                data_type = 'data'
                data = value
                data_format = obj.layer.schema.get('properties').get(key, {}).get('format')

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

                            if infos.split(';')[0].split(':')[1].split('/')[0] == 'image':
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
                    data = value

                properties.update({key: {
                    "display_value": data,
                    "type": data_type,
                    "title": obj.layer.get_property_title(key),
                    "value": obj.properties.get(key),
                    "schema": obj.layer.schema.get('properties').get(key),
                    "ui_schema": obj.layer.crud_view.ui_schema.get(key, {})
                }})

            results['__default__'] = {
                "title": "",
                "pictogram": None,
                "order": 9999,
                "properties": properties
            }

        return results

    def get_documents(self, obj):
        serializer = DocumentFeatureSerializer(obj.layer.crud_view.templates.all(),
                                               many=True,
                                               context={'request': self.context.get('request'),
                                                        'feature': obj})
        return serializer.data

    def get_geometries(self, obj):
        """ Describe geometries and action endpoint to frontend. """
        result = {
            obj.layer.name: {
                "geom": json.loads(obj.geom.geojson),
                "geom_type": obj.layer.geom_type,
                "url": reverse('feature-detail', args=(obj.layer_id, obj.identifier)),
                "identifier": obj.identifier,
                "title": _("Main geometry")
            }
        }
        for extra_geom in obj.layer.extra_geometries.all():
            geometries = obj.extra_geometries.filter(layer_extra_geom=extra_geom)
            geometry = geometries.first()
            result[extra_geom.name] = {
                "geom": json.loads(geometry.geom.geojson),
                "geom_type": extra_geom.geom_type,
                "url": reverse('feature-detail-extra-geometry', args=(obj.layer_id, obj.identifier, geometry.pk)),
                "identifier": geometry.identifier,
                "title": extra_geom.title
            } if geometry else {
                "geom": None,
                "geom_type": extra_geom.geom_type,
                "url": reverse('feature-create-extra-geometry', args=(obj.layer_id, obj.identifier, extra_geom.pk)),
                "identifier": None,
                "title": extra_geom.title
            }
        return result

    def validate_properties(self, data):
        new_data = deepcopy(data)
        # ungroup properties
        for key, value in new_data.items():
            if isinstance(value, dict):
                # pop and explode dict
                parsed_data = data.pop(key)
                for parsed_key, parsed_value in parsed_data.items():
                    data[parsed_key] = parsed_value
        # keep parent schema validation
        super().validate_properties(data)
        return data

    def save(self, **kwargs):
        super().save(**kwargs)
        # save base64 file content to storage
        store_feature_files(self.instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # expose properties in groups
        data['properties'] = self.get_properties(instance)
        return data

    class Meta(FeatureSerializer.Meta):
        exclude = ('source', 'target', 'layer',)
        fields = None


class CrudFeatureExtraGeomSerializer(FeatureExtraGeomSerializer):
    """ Used to create or edit extra geometry. Should return Feature detail serializer """

    def to_representation(self, instance):
        # use default CrudFeatureDetailSerializer to representation
        serializer = CrudFeatureDetailSerializer(instance.feature)
        return serializer.to_representation(instance.feature)

    class Meta(FeatureExtraGeomSerializer.Meta):
        fields = ('geom', )
