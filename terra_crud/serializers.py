from rest_framework import serializers
from . import models


class CrudViewSerializer(serializers.ModelSerializer):
    # TODO : include extra data for layer at creation (ex: geom_type write only)
    class Meta:
        model = models.CrudView
        fields = '__all__'


class CrudGroupSerializer(serializers.ModelSerializer):
    crud_views = CrudViewSerializer(many=True, read_only=True)

    class Meta:
        model = models.CrudGroupView
        fields = '__all__'
