from django.utils.translation import gettext as _
from rest_framework import viewsets, response
from rest_framework.views import APIView

from . import models, serializers


class CrudGroupViewSet(viewsets.ModelViewSet):
    queryset = models.CrudGroupView.objects.all().prefetch_related('crud_views__layer')
    serializer_class = serializers.CrudGroupSerializer


class CrudViewViewSet(viewsets.ModelViewSet):
    queryset = models.CrudView.objects.all()
    serializer_class = serializers.CrudViewSerializer


class CrudSettingsApiView(APIView):
    def get_general_section(self):
        return {}

    def get_menu_section(self):
        data = []
        groups = CrudGroupViewSet.queryset
        group_serializer = CrudGroupViewSet.serializer_class(groups, many=True)
        data = group_serializer.data

        # add non grouped views
        ungrouped_views = models.CrudView.objects.filter(group__isnull=True)
        views_serializer = CrudViewViewSet.serializer_class(ungrouped_views, many=True)
        data.append({
            "id": None,
            "name": _("Unclassified"),
            "order": None,
            "pictogram": None,
            "crud_views": views_serializer.data
        })
        return data

    def get(self, request, *args, **kwargs):
        data = {
            "menu": self.get_menu_section()
        }
        return response.Response(data)
