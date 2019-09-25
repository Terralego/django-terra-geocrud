from django.urls import reverse
from django.utils.http import urlunquote
from rest_framework import serializers
from geostore.serializers import LayerSerializer
from template_model.models import Template
from template_model.serializers import TemplateSerializer

from . import models


class EnrichedTemplateSerializer(TemplateSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Template
        fields = '__all__'
        extra_kwargs = {
            'added': {'read_only': True},
            'updated': {'read_only': True},
        }

    def get_url(self, obj):
        return urlunquote(reverse('terra_geocrud:render-template-pattern',
                                  kwargs={'template_pk': obj.pk}))


class CrudViewSerializer(serializers.ModelSerializer):
    """
    TODO: create layer in same time than crud view
    """
    layer = LayerSerializer()
    templates = EnrichedTemplateSerializer(many=True)

    class Meta:
        model = models.CrudView
        fields = (
            'id', 'name', 'pictogram', 'order', 'map_style',
            'form_schema', 'ui_schema', 'settings', 'layer',
            'templates',
        )


class CrudGroupSerializer(serializers.ModelSerializer):
    crud_views = CrudViewSerializer(many=True, read_only=True)

    class Meta:
        model = models.CrudGroupView
        fields = '__all__'
