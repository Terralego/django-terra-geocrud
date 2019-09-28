import json

from pathlib import Path

from rest_framework import serializers
from rest_framework.reverse import reverse

from geostore.serializers import LayerSerializer, FeatureSerializer

from . import models


class LayerViewSerializer(LayerSerializer):
    schema = None
    layer_groups = None
    routing_url = None

    class Meta(LayerSerializer.Meta):
        fields = None
        exclude = ('schema', )


class CrudViewSerializer(serializers.ModelSerializer):
    layer = LayerViewSerializer()
    feature_endpoint = serializers.SerializerMethodField()
    feature_list_properties = serializers.SerializerMethodField()
    feature_list_default_properties = serializers.SerializerMethodField()

    def get_feature_list_default_properties(self, obj):
        return obj.default_list_properties or obj.properties[:8]

    def get_feature_list_properties(self, obj):
        # TODO: override complete list with defined list
        return obj.properties

    def get_feature_endpoint(self, obj):
        return reverse('terra_geocrud:feature-list', args=(obj.layer_id, ))

    class Meta:
        model = models.CrudView
        fields = (
            'id', 'name', 'pictogram', 'order', 'map_style',
            'form_schema', 'ui_schema', 'settings', 'layer',
            'feature_endpoint', 'feature_list_properties', 'feature_list_default_properties'
        )


class CrudGroupSerializer(serializers.ModelSerializer):
    crud_views = CrudViewSerializer(many=True, read_only=True)

    class Meta:
        model = models.CrudGroupView
        fields = '__all__'


class FeatureDisplayPropertyGroup(serializers.Serializer):
    title = serializers.CharField()
    order = serializers.IntegerField()
    pictogram = serializers.ImageField()
    properties = serializers.JSONField()


class CrudFeatureListSerializer(FeatureSerializer):
    detail_url = serializers.SerializerMethodField()

    def get_detail_url(self, obj):
        return reverse('terra_geocrud:feature-detail', args=(obj.layer_id, obj.identifier))

    class Meta(FeatureSerializer.Meta):
        exclude = ('source', 'target', 'layer', )
        fields = None


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
            serializer = FeatureDisplayPropertyGroup({
                "title": group.label,
                "pictogram": group.pictogram,
                "order": group.order,
                "properties": {
                    obj.layer.get_property_title(prop):
                        obj.properties.get(prop)
                    for prop in list(group.properties)
                }
            }, context={'request': self.context.get('request')})
            results[group.slug] = serializer.data
            processed_properties += list(group.properties)
        # add default other properties
        remained_properties = list(set(crud_view.properties) - set(processed_properties))
        if remained_properties:
            serializer = FeatureDisplayPropertyGroup({
                "title": "",
                "pictogram": None,
                "order": 9999,
                "properties": {
                    obj.layer.get_property_title(prop):
                        obj.properties.get(prop)
                    for prop in list(remained_properties)
                }
            })
            results['__default__'] = serializer.data
        return results

    def get_documents(self, obj):
        results = []
        for template in obj.layer.crud_view.templates.all():
            template_path = Path(template.template_file.name)
            results.append({
                "extension": template_path.suffix,
                "template_name": template.name,
                "template_file": template_path.name,
                "download_url": reverse('terra_geocrud:render-template', args=(template.pk, obj.pk)),
            })
        return results

    class Meta(FeatureSerializer.Meta):
        exclude = ('source', 'target', 'layer',)
        fields = None
