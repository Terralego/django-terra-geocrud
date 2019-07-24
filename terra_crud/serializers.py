from rest_framework import serializers
from terracommon.terra.serializers import LayerSerializer

from . import models


class CrudViewSerializer(serializers.ModelSerializer):
    layer = LayerSerializer()

    class Meta:
        model = models.CrudView
        fields = '__all__'


class CrudGroupSerializer(serializers.ModelSerializer):
    crud_views = CrudViewSerializer(many=True, read_only=True)

    class Meta:
        model = models.CrudGroupView
        fields = '__all__'
