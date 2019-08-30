from rest_framework import serializers
from terracommon.terra.serializers import LayerSerializer

from template_model.serializers import TemplateSerializer

from . import models


class CrudViewSerializer(serializers.ModelSerializer):
    """
    TODO: create layer in same time than crud view
    """
    layer = LayerSerializer()
    template = TemplateSerializer()

    class Meta:
        model = models.CrudView
        fields = (
            'id', 'name', 'pictogram', 'order', 'map_style',
            'form_schema', 'ui_schema', 'settings', 'layer',
            'template',
        )


class CrudGroupSerializer(serializers.ModelSerializer):
    crud_views = CrudViewSerializer(many=True, read_only=True)

    class Meta:
        model = models.CrudGroupView
        fields = '__all__'
