import json

from django.utils.translation import gettext_lazy as _
from pathlib import Path
from rest_framework import serializers
from rest_framework.reverse import reverse
from template_model.models import Template

from geostore.serializers import LayerSerializer, FeatureSerializer
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
    templates = serializers.SerializerMethodField()  # DEPRECATED
    ui_schema = serializers.SerializerMethodField()
    map_style = serializers.SerializerMethodField()
    feature_endpoint = serializers.SerializerMethodField(
        help_text=_("Url endpoint for view's features")
    )
    feature_list_properties = serializers.SerializerMethodField(
        help_text=_("Available properties for feature datatable. Ordered, {name: {title, type}}")
    )

    def get_default_map_style(self, obj):
        style_settings = app_settings.TERRA_GEOCRUD.get('STYLES', {})
        if obj.layer.is_point:
            return style_settings.get('point')
        elif obj.layer.is_linestring:
            return style_settings.get('line')
        elif obj.layer.is_polygon:
            return style_settings.get('polygon')

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

    def get_templates(self, obj):
        # DEPRECATED
        return []

    def get_ui_schema(self, obj):
        """
        Original ui_schema is recomposed with grouped properties
        """
        ui_schema = obj.ui_schema.copy()

        for group in obj.feature_display_groups.all():
            # each field defined in ui schema should be placed in group key
            ui_schema[group.slug] = {'ui-order': []}

            for prop in group.properties:
                # get original definition
                original_def = ui_schema.pop(prop, None)
                if original_def:
                    ui_schema[group.slug][prop] = original_def

                # if original prop in ui-order
                if prop in ui_schema.get('ui-order', []):
                    ui_schema.get('ui-order').remove(prop)
                    ui_schema[group.slug]['ui-order'] += [prop]

            # finish by adding '*' in all cases (security)
            ui_schema[group.slug]['ui-order'] += ['*']

        return ui_schema

    def get_extent(self, obj):
        # TODO: use annotated extent
        return obj.extent

    def get_feature_list_properties(self, obj):
        # TODO: keep default properties at first, then order by property title
        default_list = obj.default_list_properties or obj.list_available_properties[:8]
        return {
            prop: {
                "title": obj.layer.get_property_title(prop),
                "selected": True if prop in default_list else False,
                "type": obj.layer.get_property_type(prop)
            }
            for prop in obj.list_available_properties
        }

    def get_feature_endpoint(self, obj):
        return reverse('terra_geocrud:feature-list', args=(obj.layer_id,))

    class Meta:
        model = models.CrudView
        fields = (
            'id', 'name', 'pictogram', 'order', 'map_style',
            'form_schema', 'ui_schema', 'settings', 'layer',
            'feature_endpoint', 'extent', 'templates', 'exports',
            'feature_list_properties',
        )


class CrudGroupSerializer(serializers.ModelSerializer):
    crud_views = CrudViewSerializer(many=True, read_only=True)

    class Meta:
        model = models.CrudGroupView
        fields = '__all__'


class FeatureDisplayPropertyGroup(serializers.ModelSerializer):
    title = serializers.CharField(source='slug')
    order = serializers.IntegerField()
    pictogram = serializers.ImageField()
    properties = serializers.SerializerMethodField()

    def get_properties(self, obj):
        """ Get feature properties in group to form { title: rendering(value) } """
        feature = self.context.get('feature')
        return {
            feature.layer.get_property_title(prop):
                feature.layer.crud_view.render_property_data(feature, prop)
            for prop in list(obj.properties)
        }

    class Meta:
        model = models.FeaturePropertyDisplayGroup
        fields = ('title', 'order', 'pictogram', 'properties')


class CrudFeatureListSerializer(FeatureSerializer):
    geom = None
    detail_url = serializers.SerializerMethodField()
    extent = serializers.SerializerMethodField()

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
    geom = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    display_properties = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    def get_geom(self, obj):
        geom = obj.geom.transform(4326, clone=True)
        return json.loads(geom.geojson)

    def get_properties(self, obj):
        results = {}
        crud_view = obj.layer.crud_view
        groups = crud_view.feature_display_groups.all()
        original_properties = obj.properties.copy()

        # get ordered groups filled
        for group in groups:
            results[group.slug] = {}
            for prop in group.properties:
                results[group.slug][prop] = original_properties.pop(prop, None)

        return {**results, **original_properties}

    def get_display_properties(self, obj):
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
            results['__default__'] = {
                "title": "",
                "pictogram": None,
                "order": 9999,
                "properties": {
                    obj.layer.get_property_title(prop): crud_view.render_property_data(obj, prop)
                    for prop in list(remained_properties)
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
        new_data = data.copy()
        # clean all dict in values
        for key in new_data:
            if isinstance(new_data[key], dict):
                # explode it
                parsed_data = new_data.pop(key)
                for parsed_key, parsed_value in parsed_data.items():
                    new_data[parsed_key] = parsed_value
        return new_data

    class Meta(FeatureSerializer.Meta):
        exclude = ('source', 'target', 'layer',)
        fields = None
