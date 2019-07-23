from rest_framework import viewsets

from . import models, serializers


class CrudGroupViewSet(viewsets.ModelViewSet):
    queryset = models.CrudGroupView.objects.all().prefetch_related('crud_views')
    serializer_class = serializers.CrudGroupSerializer


class CrudViewViewSet(viewsets.ModelViewSet):
    queryset = models.CrudView.objects.all()
    serializer_class = serializers.CrudViewSerializer
