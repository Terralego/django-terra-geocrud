import json
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path

from django.template.defaultfilters import date
from django.core.exceptions import ObjectDoesNotExist
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from geostore import settings as geostore_settings
from geostore.models import Feature, LayerExtraGeom
from geostore.serializers import FeatureSerializer, FeatureExtraGeomSerializer, GeometryFileAsyncSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis import serializers as geo_serializers
from template_model.models import Template

from . import models
from .map.styles import get_default_style
from .properties.files import store_feature_files
from .properties.utils import serialize_group_properties

# use base serializer as defined in geostore settings. using django-geostore-routing change this value

LayerSerializer = import_string(geostore_settings.GEOSTORE_LAYER_SERIALIZER)


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
    routing_settings = serializers.SerializerMethodField()

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

        for relation in obj.layer.relations_as_origin.all():
            layer = relation.destination
            try:
                related_crud_view = layer.crud_view
                view = {
                    'title': related_crud_view.name,
                    'style': related_crud_view.map_style,
                    'id_layer_vt': f'relation-{slugify(obj.layer.name)}-{slugify(relation.name)}',
                    'main': False,
                    'view_source': 'relation',
                    'pk': layer.pk
                }
                data.append(view)
            except ObjectDoesNotExist:
                pass

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
                'main': False,
                'view_source': 'extra_geometry',
                'pk': extra_layer.pk
            })
        return data

    def get_exports(self, obj):
        if not geostore_settings.GEOSTORE_EXPORT_CELERY_ASYNC:
            return None
        serializer = GeometryFileAsyncSerializer(obj.layer)
        return serializer.data

    def get_extent(self, obj):
        # TODO: use annotated extent
        return obj.extent

    def get_feature_list_properties(self, obj):
        # TODO: keep default properties at first, then order by property title
        default_list = list(obj.default_list_properties.values_list('key', flat=True)) or list(
            obj.list_available_properties.values_list('key', flat=True))[:8]
        result = {
            prop.key: {
                "title": obj.layer.get_property_title(prop.key),
                "selected": True if prop.key in default_list else False,
                "type": obj.layer.get_property_type(prop.key),
                "table_order": prop.table_order
            }
            for prop in obj.list_available_properties.all()
        }
        # order by title
        return OrderedDict(sorted(result.items(), key=lambda x: x[1]['title']))

    def get_feature_endpoint(self, obj):
        return reverse('feature-list', args=(obj.layer_id,))

    def get_routing_settings(self, obj):
        data = []
        for routing_setting in obj.routing_settings.all():
            label = routing_setting.label
            options = {}
            if routing_setting.provider == "mapbox":
                options["transit"] = routing_setting.mapbox_transit
            else:
                options["url"] = reverse('layer-route', args=[routing_setting.layer.pk])
            data.append({"label": label,
                         "provider": {
                             "name": routing_setting.provider,
                             "options": options
                         }
                         })
        return data

    class Meta:
        model = models.CrudView
        fields = (
            'id', 'name', 'object_name', 'object_name_plural',
            'pictogram', 'order', 'map_style',
            'form_schema', 'ui_schema', 'settings', 'layer',
            'feature_endpoint', 'extent', 'exports',
            'feature_list_properties', 'map_layers',
            'routing_settings'
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
            prop.key: feature.properties.get(prop.key)
            for prop in obj.group_properties.all()
        }
        editable = {prop.key: prop.editable for prop in obj.group_properties.all()}
        return serialize_group_properties(feature, final_properties, editable)

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
        keys = list(obj.layer.crud_view.list_available_properties.values_list('key', flat=True))
        return {
            key: value for key, value in obj.properties.items() if key in keys
        }

    def get_extent(self, obj):
        geom = obj.geom.transform(4326, clone=True)
        return geom.extent

    def get_detail_url(self, obj):
        return reverse('feature-detail',
                       args=(obj.layer_id, obj.identifier))

    def get_relations(self, obj):
        return {
            relation.name: reverse('feature-relation',
                                   args=(obj.layer_id, obj.identifier, relation.pk))
            for relation in obj.layer.relations_as_origin.all()
            if hasattr(relation.destination, 'crud_view')
        }

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
        feature = self.context.get('feature')
        return reverse('feature-generate-template',
                       args=(feature.layer.pk, feature.identifier, obj.pk))

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
    routing_information = serializers.JSONField(source='routing_information.route_description', required=False)

    def create(self, validated_data):
        routing_information = validated_data.pop('routing_information', {})

        feature = Feature.objects.create(**validated_data)
        models.RoutingInformations.objects.create(feature=feature,
                                                  route_description=routing_information.get('route_description',
                                                                                            {}))
        return feature

    def get_update_fields(self, instance, validated_data):
        geom = validated_data.get("geom")
        properties = validated_data.get("properties")
        update_fields = []
        if geom and geom != instance.geom:
            update_fields.append('geom')
        if properties and properties != instance.properties:
            update_fields.append('properties')
        return update_fields

    def update(self, instance, validated_data):
        route_description = validated_data.pop('routing_information', {})

        models.RoutingInformations.objects.update_or_create(feature=instance,
                                                            defaults={'route_description': route_description.get(
                                                                'route_description',
                                                                {})})
        update_fields = self.get_update_fields(instance, validated_data)
        for key in validated_data:
            setattr(instance, key, validated_data[key])
        instance.save(update_fields=update_fields)
        return instance

    def get_relations(self, obj):
        return [{"label": relation.name,
                 "order": relation.destination.crud_view.order,
                 "url": reverse('feature-relation',
                                args=(obj.layer_id, obj.identifier, relation.pk)),
                 "geojson": reverse('feature-relation',
                                    kwargs={"layer": obj.layer_id,
                                            "identifier": obj.identifier,
                                            "id_relation": relation.pk,
                                            "format": "geojson"}),
                 "crud_view_pk": relation.destination.crud_view.pk,
                 "empty": not relation.related_features.exists()
                 } for relation in obj.layer.relations_as_origin.all() if hasattr(relation.destination, 'crud_view')]

    def get_pictures(self, obj):
        """ Return feature linked pictures grouped by category, with urls to create / replace / delete """
        return [{
            "category": {
                "id": category.pk,
                "name": category.name,
            },
            "pictogram": category.pictogram.url if category.pictogram else None,
            "pictures": FeaturePictureSerializer(obj.pictures.filter(category=category),
                                                 many=True).data,
            "action_url": reverse('picture-list', args=(obj.identifier, ))
        } for category in models.AttachmentCategory.objects.all()]

    def get_attachments(self, obj):
        """ Return feature linked pictures grouped by category, with urls to create / replace / delete """
        return [{
            "category": {
                "id": category.pk,
                "name": category.name,
            },
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
            for prop in list(group.group_properties.all().values_list('key', flat=True)):
                results[group.slug][prop] = original_properties.pop(prop, None)

        return {**results, **original_properties}

    def get_display_properties(self, obj):
        """ Feature properties to display (key / value, display value and info) """
        results = {}
        crud_view = obj.layer.crud_view
        groups = crud_view.feature_display_groups.all()

        # get ordered groups filled
        for group in groups:
            serializer = FeatureDisplayPropertyGroup(group,
                                                     context={'request': self.context.get('request'),
                                                              'feature': obj})
            results[group.slug] = serializer.data

        # add default other properties
        remained_properties = crud_view.properties.filter(group__isnull=True)
        if remained_properties:
            # reconstruct property key/value list based on layer schema
            final_properties = {
                prop.key: obj.properties.get(prop.key)
                for prop in remained_properties
            }
            editable = {prop.key: prop.editable for prop in remained_properties}
            properties = serialize_group_properties(obj, final_properties, editable)

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
        old_properties = {}
        if self.instance and self.instance.pk:
            old_properties = self.instance.properties
        super().save(**kwargs)
        # save base64 file content to storage
        store_feature_files(self.instance, old_properties)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # expose properties in groups
        data['properties'] = self.get_properties(instance)
        return data

    class Meta(FeatureSerializer.Meta):
        exclude = ('source', 'target', 'layer')
        fields = None


class CrudFeatureExtraGeomSerializer(FeatureExtraGeomSerializer):
    """ Used to create or edit extra geometry. Should return Feature detail serializer """

    def to_representation(self, instance):
        # use default CrudFeatureDetailSerializer to representation
        serializer = CrudFeatureDetailSerializer(instance.feature)
        return serializer.to_representation(instance.feature)

    class Meta(FeatureExtraGeomSerializer.Meta):
        fields = ('geom', )
