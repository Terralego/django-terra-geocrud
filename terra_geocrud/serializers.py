from collections import OrderedDict
from copy import deepcopy

from django.utils.translation import gettext_lazy as _
from pathlib import Path
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis import serializers as geo_serializers
from template_model.models import Template
from geostore.serializers import LayerSerializer, FeatureSerializer
from .properties.files import get_storage, get_storage_file_path, store_data_file, get_info_content
from .properties.widgets import render_property_data
from . import models
from . import settings as app_settings


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
    extent = serializers.SerializerMethodField()
    exports = serializers.SerializerMethodField()
    ui_schema = serializers.JSONField(source='grouped_ui_schema')
    form_schema = serializers.JSONField(source='grouped_form_schema')
    map_style = serializers.SerializerMethodField()
    feature_endpoint = serializers.SerializerMethodField(
        help_text=_("Url endpoint for view's features")
    )
    feature_list_properties = serializers.SerializerMethodField(
        help_text=_("Available properties for feature datatable. Ordered, {name: {title, type}}")
    )

    def get_default_map_style(self, obj):
        style_settings = app_settings.TERRA_GEOCRUD.get('STYLES', {})
        response = {}
        if obj.layer.is_point:
            response = style_settings.get('point')
        elif obj.layer.is_linestring:
            response = style_settings.get('line')
        elif obj.layer.is_polygon:
            response = style_settings.get('polygon')
        return response

    def get_map_style(self, obj):
        style = obj.map_style
        return style if style else self.get_default_map_style(obj)

    def get_exports(self, obj):
        return [{
            "name": "shapefile",
            "url": reverse('geostore:layer-shapefile', args=[obj.layer_id, ])
        }, {
            "name": "geojson",
            "url": reverse('geostore:layer-geojson', args=[obj.layer_id, ])
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
        return reverse('terra_geocrud:feature-list', args=(obj.layer_id,))

    class Meta:
        model = models.CrudView
        fields = (
            'id', 'name', 'pictogram', 'order', 'map_style',
            'form_schema', 'ui_schema', 'settings', 'layer',
            'feature_endpoint', 'extent', 'exports',
            'feature_list_properties',
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
        widget_properties = self.context.get('widget_properties')
        final_properties = {
            prop: feature.properties.get(prop)
            for prop in list(obj.properties)
        }

        # apply widgets
        for widget in widget_properties.filter(property__in=obj.properties):
            final_properties[widget.property] = render_property_data(feature, widget)

        return {
            feature.layer.get_property_title(key): value
            for key, value in final_properties.items()
        }

    class Meta:
        model = models.FeaturePropertyDisplayGroup
        fields = ('title', 'slug', 'order', 'pictogram', 'properties')


class CrudFeatureListSerializer(FeatureSerializer):
    geom = None
    detail_url = serializers.SerializerMethodField()
    extent = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    def get_properties(self, obj):
        """ Keep only properties that can be shonwed in list """
        list_available_properties = list(obj.layer.crud_view.list_available_properties)
        return {
            key: value for key, value in obj.properties.items() if key in list_available_properties
        }

    def get_extent(self, obj):
        geom = obj.geom.transform(4326, clone=True)
        return geom.extent

    def get_detail_url(self, obj):
        return reverse('terra_geocrud:feature-detail',
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
        return reverse('terra_geocrud:render-template',
                       args=(obj.pk, self.context.get('feature').pk))

    class Meta:
        fields = (
            'extension', 'template_name', 'template_file', 'download_url'
        )
        model = Template


class CrudFeatureDetailSerializer(FeatureSerializer):
    title = serializers.SerializerMethodField()
    geom = geo_serializers.GeometryField()
    documents = serializers.SerializerMethodField()
    display_properties = serializers.SerializerMethodField()
    properties = serializers.JSONField()

    def get_title(self, obj):
        """ Get Feature title, as feature_title_property content or identifier by default """
        crud_view_defined_property = obj.layer.crud_view.feature_title_property
        return obj.properties.get(crud_view_defined_property, '') if crud_view_defined_property else obj.identifier

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
        """ Feature properties to display (title / rendered value) """
        processed_properties = []
        results = {}
        crud_view = obj.layer.crud_view
        groups = crud_view.feature_display_groups.all()
        widget_properties = crud_view.feature_property_rendering.all()

        # get ordered groups filled
        for group in groups:
            serializer = FeatureDisplayPropertyGroup(group,
                                                     context={'request': self.context.get('request'),
                                                              'feature': obj,
                                                              'widget_properties': widget_properties})
            results[group.slug] = serializer.data
            processed_properties += list(group.properties)

        # add default other properties
        remained_properties = list(set(crud_view.properties) - set(processed_properties))
        if remained_properties:
            final_properties = {
                prop: obj.properties.get(prop)
                for prop in list(remained_properties)
            }
            # apply widgets
            for widget in widget_properties.filter(property__in=remained_properties):
                final_properties[widget.property] = render_property_data(obj, widget)

            results['__default__'] = {
                "title": "",
                "pictogram": None,
                "order": 9999,
                "properties": {
                    obj.layer.get_property_title(key): value for key, value in final_properties.items()
                }
            }
        return results

    def get_documents(self, obj):
        serializer = DocumentFeatureSerializer(obj.layer.crud_view.templates.all(),
                                               many=True,
                                               context={'request': self.context.get('request'),
                                                        'feature': obj})
        return serializer.data

    def validate_properties(self, data):
        new_data = deepcopy(data)
        # degroup properties
        for key, value in new_data.items():
            if isinstance(value, dict):
                # pop and explode dict
                parsed_data = data.pop(key)
                for parsed_key, parsed_value in parsed_data.items():
                    data[parsed_key] = parsed_value
        # keep parent schema validation
        super().validate_properties(data)
        return data

    def _store_files(self):
        files_properties = [
            key for key, value in self.instance.layer.schema['properties'].items()
            if self.instance.layer.schema['properties'][key].get('format') == 'data-url'
        ]
        if files_properties:
            storage = get_storage()
            for file_prop in files_properties:
                value = self.instance.properties.get(file_prop)
                if value:
                    storage_file_path = get_storage_file_path(file_prop, value, self.instance)
                    file_info, file_content = get_info_content(value)
                    store_data_file(storage, storage_file_path, file_content)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._store_files()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # expose properties in groups
        data['properties'] = self.get_properties(instance)
        return data

    class Meta(FeatureSerializer.Meta):
        exclude = ('source', 'target', 'layer',)
        fields = None
